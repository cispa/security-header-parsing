from typing import List

from datetime import datetime
import json

from sqlalchemy.orm import mapped_column, Mapped, declarative_base, relationship, sessionmaker
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, UniqueConstraint, Enum, create_engine
from sqlalchemy.dialects.postgresql import JSONB


# Setup the config
try:    
    proj_config= json.load(open("config.json"))
except OSError:
    proj_config= json.load(open("_hp/tools/config.json"))

DB_URL = proj_config['DB_URL']
SECRET = proj_config['SECRET']


# DB
Base = declarative_base()


class BaseModel(Base):
    """Base model each model inherits from."""
    __abstract__ = True
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestCase(BaseModel):
    """Model for all implemented tests."""
    __tablename__ = 'TestCase'
    id = Column(Integer, primary_key=True)   
    # feature_group: e.g., Framing, Script Execution, ...
    feature_group = Column(String)
    # test_file: name of the file this tests is in 
    test_file = Column(String)
    # test_name: e.g., cross-origin simple framing, ...
    test_name = Column(String)
    # Additional Information (?)
    additional_info = Column(String)
    
    # Helper
    result = relationship('Result', back_populates='testcase')

    # Combination of feature_group, test_file, test_name should be unique
    __table_args__ = (
        UniqueConstraint('feature_group', 'test_file', 'test_name', name='uq_test'),
    )


class Browser(BaseModel):
    """Model to save information of each tested browser."""
    __tablename__ = 'Browser'
    id: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String)
    version = Column(String)
    os = Column(String)

    # Helper
    result: Mapped[List["Result"]] = relationship(back_populates='browser')

     # Combination of name, version, os should be unique
    __table_args__ = (
        UniqueConstraint('name', 'version', 'os', name='uq_browser'),
    )


class Response(BaseModel):
    """Model to save information about the tested responses."""
    __tablename__ = 'Response'
    id = Column(Integer, primary_key=True)
    # Raw header information as JSON: [("X-Test", "PASS"), ("Content-Type", "text/plain")]
    raw_header = Column(JSONB)
    # The status code WPT should use
    status_code = Column(Integer, default=200)
    # TODO: additional information about a response
    # E.g., for framing we have different "groups" of responses we test: XFO only, CSP-FA only, XFO vs. CSP-FA, ...
    # We have to define somewhere which label responses we use for which test_file tests?
    label = Column(String)

    # Helper
    result = relationship('Result', back_populates='response')
     
    # Combination of header, status_code, http_ver, label should be unique
    __table_args__ = (
        UniqueConstraint('raw_header', 'status_code', 'label', name='uq_response'),
    )

# All the above tables get created before we run the tests
# Only the result table below is filled during the experiment

class Result(BaseModel):
    """Model to save the results of our tests."""
    __tablename__ = 'Result'
    id = Column(Integer, primary_key=True)
    # Result of the test
    # outcome_type: Type of result value (e.g., Int, undefined, ..) (mostly object as the outcome should be JSON)
    outcome_type = Column(String)
    # outcome_value: JSONB result value 
    outcome_value = Column(JSONB)

    # Provided by testharness.js
    test_name = Column(String)   # TODO: Alternative for testcase_id? Otherwise we need to figure out how each wpt-test knows it's own testcase_id, problem: includes resp_id and URL?
    test_status = Column(Integer)
    test_message = Column(String)
    test_stack = Column(String)

    # Origin relations 
    org_scheme = Column(Enum('http:', 'https:', 'http2', name='scheme'))
    org_host = Column(String) # Should always be sub.headers.websec.saarland!
    resp_scheme = Column(Enum('http:', 'https:', 'http2', name='scheme'))
    resp_host = Column(String) # Should be one of sub.headers.websec.saarland (same-orgin), headers.websec.saarland (parent-domain; same-site), sub.sub.headers.websec.saarland (sub-domain; same-site), or headers.webappsec.eu (cross-site)
    relation_info = Column(String) # E.g., direct, sandbox/srcdoc, nested (chain), nested (parent), nested (top-level)

    # Foreign keys
    browser_id: Mapped[int] = mapped_column(ForeignKey("Browser.id"))
    testcase_id: Mapped[int] = mapped_column(ForeignKey("TestCase.id"))
    response_id: Mapped[int] = mapped_column(ForeignKey("Response.id"))
    browser: Mapped["Browser"] = relationship(back_populates="result")
    testcase: Mapped["TestCase"] = relationship(back_populates="result")
    response: Mapped["Response"] = relationship(back_populates="result")

    # All tests that we have to run are:
    # TestCase * Browser * Response (subset of responses relevant for the selected TestCase)
    # TODO: how do we want to run these?
    # 1. Precreate all and select ones that are not yet processed for each run?
    # 2. Distribute IDs to each run and have them filled one by one (Currenty implemented?)
    # 3. Something else?
    status = Column(Enum('FREE', 'PROCESSING', 'FINISHED', name='status'))

# Run the DB Stuff 
# Create a SQLAlchemy engine
engine = create_engine(DB_URL)

# Create the tables in the database
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)

# Create dummy data entries
if __name__ == "__main__":
    with Session() as session:
        # Always make sure that the unknown browser exist with ID=1!
        b: Browser = Browser(name="Unknown", version="Unknown", os="Unknown")
        t: TestCase = TestCase(feature_group="Unknown", test_file="Unknown", test_name="Unknown")
        r: Response = Response(raw_header=[("X-Frame-Options", "SAMEORIGIN"), ("Content-Type", "text/html")], status_code=200, label="Unknown")
        session.add_all([b,t,r])
        session.commit()