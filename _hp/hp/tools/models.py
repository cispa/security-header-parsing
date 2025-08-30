from typing import List

from datetime import datetime
import json

from sqlalchemy.orm import mapped_column, Mapped, declarative_base, relationship, sessionmaker
from sqlalchemy import Column, LargeBinary, String, Integer, ForeignKey, DateTime, UniqueConstraint, Enum, create_engine
from sqlalchemy.dialects.postgresql import JSONB



# Setup the config
try:
	proj_config = json.load(open("config.json"))
except OSError:
	try:
		proj_config = json.load(open("/app/_hp/hp/tools/config.json"))
	except OSError:
		proj_config = json.load(open("../config.json"))

DB_URL = proj_config['DB_URL']

try:
	wpt_config = json.load(open("/app/_hp/wpt-config.json"))
except OSError:
	try:
		wpt_config = json.load(open("../../wpt-config.json"))
	except OSError:
		wpt_config = json.load(open("../../../wpt-config.json"))

base_host = wpt_config['browser_host']
alt_host = wpt_config['alternate_hosts']['alt']

# DB
Base = declarative_base()


class BaseModel(Base):
    """Base model each model inherits from including timestamps."""
    __abstract__ = True
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class TestCase(BaseModel):
    """Model for all implemented tests (unused)."""
    __tablename__ = 'TestCase'
    id = Column(Integer, primary_key=True)
    # feature_group: e.g., Framing, Script Execution, ...
    feature_group = Column(String)
    # test_file: name of the file this tests is in
    test_file = Column(String)
    # test_name: e.g., cross-origin simple framing, ...
    test_name = Column(String)
    # Additional Information
    additional_info = Column(String)

    # Helper
    result = relationship('Result', back_populates='testcase')

    # Combination of feature_group, test_file, test_name should be unique
    __table_args__ = (
        UniqueConstraint('feature_group', 'test_file',
                         'test_name', name='uq_test'),
    )


class Browser(BaseModel):
    """Model to save information of each tested browser configuration."""
    __tablename__ = 'Browser'
    id: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String)
    version = Column(String)
    os = Column(String)
    headless_mode = Column(
        Enum('real', 'xvfb', 'headless', 'headless-new', name='headless_mode'))
    automation_mode = Column(Enum(
        'manual', 'intent', 'selenium', 'playwright', 'other', name='automation_mode'))
    # Space for additional information about a browser configuration
    add_info = Column(String)

    # Helper
    result: Mapped[List["Result"]] = relationship(back_populates='browser')

    # Combination of name, version, os should be unique
    __table_args__ = (
        UniqueConstraint('name', 'version', 'os', 'headless_mode',
                         'automation_mode', name='uq_browser'),
    )


class Response(BaseModel):
    """Model to save information about the tested responses."""
    __tablename__ = 'Response'
    id = Column(Integer, primary_key=True)
    # Raw header information as JSON: [("X-Test", "PASS"), ("Content-Type", "text/plain")]
    raw_header = Column(LargeBinary)
    # The status code WPT should use
    status_code = Column(Integer, default=200)
    # Additional information about a response
    # E.g., for framing we have different "groups" of responses we test: XFO only, CSP-FA only, XFO vs. CSP-FA, ...
    label = Column(String)

    # RespType: debug (allow/deny only for debug), basic (small set of well-defined values for testing all combinations), parsing (large set of responses, do not run all combinations with them!)
    resp_type = Column(Enum('debug', 'basic', 'parsing', name='resp_type'))

    # Helper
    result = relationship('Result', back_populates='response')

    # Combination of header, status_code, http_ver, label should be unique
    __table_args__ = (
        UniqueConstraint('raw_header', 'status_code', 'label',
                         'resp_type', name='uq_response'),
    )


# All the above tables get filled before we run any of the tests
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

    # Provided by testharness.sub.js
    # Alternative for testcase_id:
    test_name = Column(String)
    test_status = Column(Integer)
    test_message = Column(String)
    test_stack = Column(String)

    # Origin relations
    org_scheme = Column(Enum('http', 'https', 'http2', name='scheme'))
    # Should always be sub.{base_host}!
    org_host = Column(Enum(f'sub.{base_host}', '', name='ohost'))
    resp_scheme = Column(Enum('http', 'https', 'http2', name='scheme'))
    # Should be one of sub.{base_host} (same-orgin), {base_host} (parent-domain; same-site), sub.sub.{base_host} (sub-domain; same-site), or {alt_host} (cross-site)
    resp_host = Column(Enum(f'sub.{base_host}', f'sub.sub.{base_host}',
                       f'{base_host}', f'{alt_host}', name='rhost'))
    # E.g., direct, sandbox/srcdoc, nested (chain), nested (parent), nested (top-level), or something else
    relation_info = Column(String)

    # Foreign keys
    browser_id: Mapped[int] = mapped_column(ForeignKey("Browser.id"))
    testcase_id: Mapped[int] = mapped_column(ForeignKey("TestCase.id"))
    response_id: Mapped[int] = mapped_column(ForeignKey("Response.id"))
    browser: Mapped["Browser"] = relationship(back_populates="result")
    testcase: Mapped["TestCase"] = relationship(back_populates="result")
    response: Mapped["Response"] = relationship(back_populates="result")

    status = Column(Enum('FREE', 'PROCESSING', 'FINISHED', name='status'))

    # For easier manual debugging
    full_url = Column(String)


# Create the DB
# Create a SQLAlchemy engine
engine = create_engine(DB_URL)

# Create the tables in the database
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)

# Create dummy data entries
if __name__ == "__main__":
    from hp.tools.crawler.utils import get_or_create
    with Session() as session:
        # Always make sure that the unknown browser exist with ID=1!
        b = get_or_create(session, Browser, name="Unknown", version="Unknown",
                             os="Unknown", headless_mode="real", automation_mode="manual")
        t = get_or_create(session, TestCase, feature_group="Unknown",
                               test_file="Unknown", test_name="Unknown")
        r = get_or_create(session, Response, raw_header=json.dumps([("X-Frame-Options", "SAMEORIGIN"), ("Content-Type",
                               "text/html")]).encode("utf-8"), status_code=200, label="Unknown", resp_type="debug")
        print(b, t, r)
