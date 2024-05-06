from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Define a base class for declarative class definitions
Base = declarative_base()


# Define SQLAlchemy models for each table
class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)


class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    typeid = Column(Integer, ForeignKey('problem_type.id'), nullable=False)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False)
    notes = Column(Text)
    level = Column(String)
    companies = Column(String)
    remarks = Column(String)
    concepts = Column(String)
    date_added = Column(TIMESTAMP)
    filename = Column(String)
    subdirectory = Column(String)
    sheet_item_id = Column(Integer, ForeignKey('sheet_section_item.uid'))
    include_count = Column(Boolean, default=True, nullable=False)
    # Define the inverse relationship with ProblemType
    type = relationship("ProblemType", back_populates="problems")


class Platform(Base):
    __tablename__ = 'platforms'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    icon = Column(String, nullable=False)


class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    logo = Column(String)
    color_light = Column(String)
    color_dark = Column(String)


class Remark(Base):
    __tablename__ = 'remarks'

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)


class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)


class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    recurrence = Column(String, nullable=False)
    start_time = Column(String)
    end_time = Column(String)
    date = Column(String)


class ProblemType(Base):
    __tablename__ = 'problem_type'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    # Define a one-to-many relationship with Problem
    problems = relationship("Problem", back_populates="type")


class Tracker(Base):
    __tablename__ = 'trackers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    level = Column(String, nullable=False)


class MailLog(Base):
    __tablename__ = 'maillog'

    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    recipient = Column(String, nullable=False)
    date = Column(String)


class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    filename = Column(String)
    extension = Column(String)


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default='TODO')
    sections = relationship("PlaylistSection", back_populates="playlist")


class PlaylistSection(Base):
    __tablename__ = 'playlist_section'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    playlist_uid = Column(String, ForeignKey('playlist.uid'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default='TODO')
    playlist = relationship("Playlist", back_populates="sections")
    items = relationship("PlaylistItem", back_populates="section")


class PlaylistItem(Base):
    __tablename__ = 'playlist_item'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    section_uid = Column(String, ForeignKey('playlist_section.uid'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default='TODO')
    image = Column(String)
    url = Column(String)
    content = Column(Text)
    content_type = Column(String)
    section = relationship("PlaylistSection", back_populates="items")


class Sheet(Base):
    __tablename__ = 'sheet'
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String)
    url = Column(String)
    image = Column(String)
    sections = relationship("SheetSection", back_populates="sheet")


class SheetSection(Base):
    __tablename__ = 'sheet_section'
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default="TODO")
    sheet_uid = Column(String, ForeignKey('sheet.uid'), nullable=False)
    sheet = relationship("Sheet", back_populates="sections")
    items = relationship("SheetSectionItem", back_populates="section")


class SheetSectionItem(Base):
    __tablename__ = 'sheet_section_item'
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    url = Column(String)
    description = Column(String)
    level = Column(String)
    companies = Column(String)
    concepts = Column(String)
    status = Column(String, nullable=False, default="TODO")
    sheet_section_uid = Column(String, ForeignKey('sheet_section.uid'), nullable=False)
    section = relationship("SheetSection", back_populates="items")
