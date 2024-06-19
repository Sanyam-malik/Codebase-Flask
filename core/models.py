from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Boolean, Index, DateTime, func, Float, \
    Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import utility

# Define a base class for declarative class definitions
Base = declarative_base()


class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    author_index = Index('idx_quotes_author', author)
    content_index = Index('idx_quotes_content', content)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            author=data.get('author', None),
            content=data.get('content', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'author': self.author,
            'content': self.content
        }


class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
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
    sheet_item_status = Column(String)
    include_count = Column(Boolean, default=True, nullable=False)
    type = relationship("ProblemType", back_populates="problems")

    typeid_index = Index('idx_problems_typeid', typeid)
    status_index = Index('idx_problems_status', status)
    name_index = Index('idx_problems_name', name)
    remarks_index = Index('idx_problems_remarks', remarks)
    levels_index = Index('idx_problems_level', level)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            name=data.get('name', None),
            description=data.get('description', None),
            typeid=data.get('typeid', None),
            url=data.get('url', None),
            status=data.get('status', None),
            notes=data.get('notes', None),
            level=data.get('level', None),
            companies=data.get('companies', None),
            remarks=data.get('remarks', None),
            concepts=data.get('concepts', None),
            date_added=data.get('date_added', None),
            filename=data.get('filename', None),
            subdirectory=data.get('subdirectory', None),
            sheet_item_status=data.get('sheet_item_status', None),
            include_count=data.get('include_count', True)
        )

    def __response_json__(self, include_RR=False):
        obj = {
            'id': self.uid,
            'name': self.name,
            'slug': utility.create_slug(self.name),
            'type': self.type.__response_json__(include_RR),
            'description': self.description,
            'url': self.url,
            'level': self.level,
            'status': self.status,
            'notes': self.notes,
            'date': str(self.date_added),
            'filename': self.filename,
            'companies': self.companies,
            'remarks': self.remarks,
            'sheet_item_status':self.sheet_item_status,
            'subdirectory': self.subdirectory
        }
        return obj


class Platform(Base):
    __tablename__ = 'platforms'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    icon = Column(String, nullable=False)

    name_index = Index('idx_platforms_name', name)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            name=data.get('name', None),
            url=data.get('url', None),
            icon=data.get('icon', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'name': self.name,
            'url': self.url,
            'icon': self.icon,
            'slug': utility.create_slug(self.name)
        }

    def __data_store__(self):
        return {
            'name': self.name,
            'url': self.url,
            'icon': self.icon
        }


class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    logo = Column(String)
    color_light = Column(String)
    color_dark = Column(String)

    name_index = Index('idx_companies_name', name)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            name=data.get('name', None),
            logo=data.get('logo', None),
            color_light=data.get('color_light', None),
            color_dark=data.get('color_dark', None)
        )

    def __response_json__(self):
        return {
            'name': self.name,
            'id': self.uid,
            'logo': self.logo,
            'color_light': self.color_light,
            'color_dark': self.color_dark,
            'slug': utility.create_slug(self.name)
        }


class Level(Base):
    __tablename__ = 'levels'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    level = Column(Text, nullable=False)

    level_index = Index('idx_levels_level', level)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            level=data.get('level', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'level': self.level,
            'slug': utility.create_slug(self.level)
        }


class Status(Base):
    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    status = Column(Text, nullable=False)

    status_index = Index('idx_statuses_status', status)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            status=data.get('status', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'status': self.status,
            'slug': utility.create_slug(self.status)
        }


class Remark(Base):
    __tablename__ = 'remarks'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    text = Column(Text, nullable=False)

    text_index = Index('idx_remarks_text', text)
    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid'),
            text=data.get('text')
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'remark': self.text,
            'slug': utility.create_slug(self.text)
        }


class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    key_index = Index('idx_settings_key', key)

    @classmethod
    def from_json(cls, data):
        return cls(
            key=data.get('key', None),
            value=data.get('value', None)
        )

    def __response_json__(self):
        return {
            'name': self.key,
            'config': self.value
        }


class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    recurrence = Column(String, nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)
    date = Column(Date)

    name_index = Index('idx_reminders_name', name)
    start_time_index = Index('idx_reminders_start_time', start_time)
    end_time_index = Index('idx_reminders_end_time', end_time)
    date_index = Index('idx_reminders_date', date)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            name=data.get('name', None),
            description=data.get('description', None),
            recurrence=data['recurrence', None],
            start_time=data.get('start_time', None),
            end_time=data.get('end_time', None),
            date=data.get('date', None)
        )

    @staticmethod
    def _parse_time(time_str):
        if time_str:
            return datetime.strptime(time_str, "%H:%M").time()
        return None

    @staticmethod
    def _parse_date(date_str):
        if date_str:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        return None

    def __response_json__(self):
        return {
            'id': self.uid,
            'name': self.name,
            'description': self.description,
            'recurrence': self.recurrence,
            'start_time': self.start_time.strftime("%H:%M") if self.start_time else None,
            'end_time': self.end_time.strftime("%H:%M") if self.end_time else None,
            'date': self.date.strftime("%Y-%m-%d") if self.date else None
        }

    def __data_store__(self):
        return {
            'name': self.name,
            'description': self.description,
            'recurrence': self.recurrence,
            'start_time': self.start_time.strftime("%H:%M") if self.start_time else None,
            'end_time': self.end_time.strftime("%H:%M") if self.end_time else None,
            'date': self.date.strftime("%Y-%m-%d") if self.date else None
        }


class ProblemType(Base):
    __tablename__ = 'problem_type'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    problems = relationship("Problem", back_populates="type")

    name_index = Index('idx_problem_type_name', name)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            name=data.get('name', None),
            description=data.get('description', None)
        )

    def __response_json__(self, include_RR=True):
        if include_RR:
            obj = {
                'id': self.uid,
                'name': self.name,
                'slug': utility.create_slug(self.name),
                'description': self.description,
                'problems': [problem.__response_json__() for problem in self.problems]
            }
        else:
            obj = {
                'id': self.uid,
                'name': self.name,
                'slug': utility.create_slug(self.name),
                'description': self.description,
            }
        return obj


class Tracker(Base):
    __tablename__ = 'trackers'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    level = Column(String, nullable=False)

    name_index = Index('idx_tracker_name', name)
    level_index = Index('idx_tracker_level', level)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            name=data.get('name', None),
            level=data.get('level', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'name': self.name,
            'slug': utility.create_slug(self.name),
            'level': self.level
        }

    def __data_store__(self):
        return {
            'name': self.name,
            'level': self.level
        }


class MailLog(Base):
    __tablename__ = 'maillog'

    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    recipient = Column(String, nullable=False)
    date = Column(String)

    subject_index = Index('idx_maillog_subject', subject)
    recipient_index = Index('idx_maillog_recipient', recipient)

    @classmethod
    def from_json(cls, data):
        return cls(
            subject=data.get('subject', None),
            body=data.get('body', None),
            recipient=data.get('recipient', None),
            date=data.get('date', None)
        )

    def __response_json__(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'body': self.body,
            'recipient': self.recipient,
            'date': self.date
        }


class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    items = relationship("NoteItem", back_populates="note", cascade='all, delete-orphan')

    title_index = Index('idx_notes_title', title)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            title=data.get('title', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'title': self.title,
            'slug': utility.create_slug(self.title),
            'items': [item.__response_json__() for item in self.items]
        }


class NoteItem(Base):
    __tablename__ = 'note_item'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    filename = Column(String, nullable=False)
    extension = Column(String, nullable=False)
    note_id = Column(Integer, ForeignKey('notes.id'), nullable=False)
    note = relationship("Note", back_populates="items")

    filename_index = Index('idx_note_item_filename', filename)
    extension_index = Index('idx_note_item_extension', extension)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            filename=data.get('filename', None),
            extension=data.get('extension', None),
            note_id=data.get('note_id', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'url': self.filename,
            'extension': self.extension
        }


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    total_items_count = Column(Integer, default=0, nullable=False)
    completed_items_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    sections = relationship("PlaylistSection", back_populates="playlist", cascade='all, delete-orphan')

    title_index = Index('idx_playlist_title', title)

    @classmethod
    def from_json(cls, data):
        created_at = datetime.fromisoformat(data.get('created_at')) if 'created_at' in data else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if 'updated_at' in data else None
        return cls(
            uid=data.get('id', None),
            title=data.get('title', None),
            description=data.get('description', None),
            total_items_count=data.get('total_items', None),
            created_at=created_at,
            updated_at=updated_at
        )

    def __response_json__(self):
        return {
                'id': self.uid,
                'title': self.title,
                'description': self.description,
                'total_items': self.total_items_count,
                'completed_items': self.completed_items_count,
                'complete_percent': int((self.completed_items_count / self.total_items_count) * 100) if self.total_items_count > 0 else 0,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'sections': [section.__response_json__() for section in self.sections]
            }


class PlaylistSection(Base):
    __tablename__ = 'playlist_section'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    playlist_uid = Column(String, ForeignKey('playlist.uid'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default='TODO')
    playlist = relationship("Playlist", back_populates="sections")
    items = relationship("PlaylistItem", back_populates="section", cascade='all, delete-orphan')

    playlist_uid_index = Index('idx_playlist_section_playlist_uid', playlist_uid)
    title_index = Index('idx_playlist_section_title', title)
    status_index = Index('idx_playlist_section_status', status)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('id', None),
            title=data.get('title', None),
            description=data.get('description', None),
            playlist_uid=data.get('playlist_uid', None),
            status=data.get('status', 'TODO')
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'items': [item.__response_json__() for item in self.items]
        }


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

    section_uid_index = Index('idx_playlist_item_section_uid', section_uid)
    title_index = Index('idx_playlist_item_title', title)
    status_index = Index('idx_playlist_item_status', status)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('id', None),
            section_uid=data.get('section_uid', None),
            title=data.get('title', None),
            description=data.get('description', None),
            status=data.get('status', 'TODO'),
            image=data.get('image', None),
            url=data.get('url', None),
            content=data.get('content', None),
            content_type=data.get('content_type', None)
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'url': self.url,
            'image': self.image,
            'content': self.content,
            'content_type': self.content_type,
            'type': self.content_type
        }


class Sheet(Base):
    __tablename__ = 'sheet'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String)
    url = Column(String)
    image = Column(String)
    total_items_count = Column(Integer, default=0, nullable=False)
    completed_items_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    sections = relationship("SheetSection", back_populates="sheet", cascade='all, delete-orphan')

    @classmethod
    def from_json(cls, data):
        created_at = datetime.fromisoformat(data.get('created_at')) if 'created_at' in data else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if 'updated_at' in data else None
        return cls(
            uid=data.get('id', None),
            name=data.get('title', None),
            description=data.get('description', None),
            url=data.get('url', None),
            image=data.get('image', None),
            total_items_count=data.get('total_items', None),
            created_at=created_at,
            updated_at=updated_at
        )

    def __response_json__(self):

        return {
            'id': self.uid,
            'title': self.name,
            'description': self.description,
            'url': self.url,
            'image': self.image,
            'total_items': self.total_items_count,
            'completed_items': self.completed_items_count,
            'complete_percent': int((self.completed_items_count / self.total_items_count) * 100) if self.total_items_count > 0 else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sections': [section.__response_json__() for section in self.sections]
        }


class SheetSection(Base):
    __tablename__ = 'sheet_section'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default="TODO")
    sheet_uid = Column(String, ForeignKey('sheet.uid'), nullable=False)
    sheet = relationship("Sheet", back_populates="sections")
    items = relationship("SheetSectionItem", back_populates="section", cascade='all, delete-orphan')

    sheet_uid_index = Index('idx_sheet_section_sheet_uid', sheet_uid)
    status_index = Index('idx_sheet_section_status', status)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('id', None),
            name=data.get('title', None),
            description=data.get('description', None),
            sheet_uid=data.get('sheet_uid', None),
            status=data.get('status', 'TODO')
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'title': self.name,
            'description': self.description,
            'status': self.status,
            'items': [item.__response_json__() for item in self.items]
        }


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
    frequency = Column(Float, default=None)
    sheet_section_uid = Column(String, ForeignKey('sheet_section.uid'), nullable=False)
    section = relationship("SheetSection", back_populates="items")
    response = relationship("SheetSectionItemResponse", back_populates="sheet_section_item", cascade='all, delete-orphan')

    sheet_section_uid_index = Index('idx_sheet_section_item_sheet_section_uid', sheet_section_uid)
    status_index = Index('idx_sheet_section_item_status', status)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('id', None),
            name=data.get('title', None),
            url=data.get('url', None),
            description=data.get('description', None),
            level=data.get('level', None),
            companies=data.get('companies', None),
            concepts=data.get('concepts', None),
            status=data.get('status', 'TODO') if 'status' in data else 'TODO',
            sheet_section_uid=data.get('sheet_section_uid', None)
        )

    def __response_json__(self):
        obj = {
            'id': self.uid,
            'title': self.name,
            'description': self.description,
            'status': self.status,
            'url': self.url,
            'level': self.level,
            'companies': str(self.companies).split(":"),
            'concepts': str(self.concepts).split(":"),
            'problem': self.response[0].__response_json__() if self.response else None
        }
        return obj


class SheetSectionItemResponse(Base):
    __tablename__ = 'sheet_section_item_response'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    sheet_section_item_id = Column(String, ForeignKey('sheet_section_item.uid'), nullable=False)
    problem_id = Column(String, ForeignKey('problems.uid'), nullable=False)

    sheet_section_item = relationship("SheetSectionItem", back_populates="response")
    problem = relationship("Problem")

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('uid', None),
            sheet_section_item_id=data.get('sheet_section_item_id', None),
            problem_id=data.get('problem_id', None)
        )

    def __response_json__(self):
        return self.problem.__response_json__() if self.problem else None
