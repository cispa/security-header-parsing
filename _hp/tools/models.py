from typing import List

from datetime import datetime
import json

from sqlalchemy.orm import mapped_column, Mapped, declarative_base, relationship, sessionmaker
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, UniqueConstraint, Enum, create_engine
from sqlalchemy.dialects.postgresql import JSONB


# Setup the config
try:
    proj_config= json.load(open("../config.json"))
except OSError:
    proj_config= json.load(open("_hp/config.json"))

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
    # HTTP version of the response;
    # TODO: We cannot change the http_ver of a response but have to decide earlier which server/endpoint we are using?
    http_ver = Column(String, default="1.1")
    # TODO: additional information about a response
    # E.g., for framing we have different "groups" of responses we test: XFO only, CSP-FA only, XFO vs. CSP-FA, ...
    # We have to define somewhere which label responses we use for which test_file tests?
    label = Column(String)

    # Helper
    result = relationship('Result', back_populates='response')
     
    # Combination of header, status_code, http_ver, label should be unique
    __table_args__ = (
        UniqueConstraint('raw_header', 'status_code', 'http_ver', 'label', name='uq_response'),
    )

# All the above tables get created before we run the tests
# Only the result table below is filled during the experiment

class Result(BaseModel):
    """Model to save the results of our tests."""
    __tablename__ = 'Result'
    id = Column(Integer, primary_key=True)
    # Result of the test
    # outcome_type: Type of result value (e.g., Int, undefined, ..)
    outcome_type = Column(String)
    # outcome_value: JSONB result value (TODO: not sure if this is the best idea?!)
    outcome_value = Column(JSONB)

    # Provided by testharness.js
    test_name = Column(String)   # TODO: Alternative for testcase_id? Otherwise we need to figure out how each wpt-test knows it's own testcase_id
    test_status = Column(Integer)
    test_message = Column(String)
    test_stack = Column(String)  # Is String the best for this column?

    # TODO: add the origin relations maybe? Simple framing is the same test and the difference is from which origin the response is coming?


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
        b: Browser = Browser(name="Unknown", version="Unknown", os="Unknown")
        t: TestCase = TestCase(feature_group="Unknown", test_file="Unknown", test_name="Unknown")
        r: Response = Response(raw_header=[("X-Frame-Options", "SAMEORIGIN"), ("Content-Type", "text/html")], status_code=200, http_ver="1.1", label="Unknown")
        session.add_all([b,t,r])
        session.commit()