from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index, DateTime, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
# Define a base class for declarative class definitions
Base = declarative_base()


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    total_items_count = Column(Integer, default=0, nullable=False)
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
            sheet_section_uid=data.get('sheet_section_uid', None),
            frequency=data.get('frequency', None)
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
            'frequency': self.frequency
        }
        return obj
