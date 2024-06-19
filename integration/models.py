from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Chats(Base):
    __tablename__ = 'conversation'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    problem_slug = Column(String)
    role = Column(String, nullable=False, default="user")
    content = Column(Text, nullable=False, default="")

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('id'),
            problem_slug=data.get('problem_slug'),
            role=data.get('role', 'user'),
            content=data.get('content', '')
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'problem_slug': self.problem_slug,
            'role': self.role,
            'content': self.content
        }


class VideoSolutions(Base):
    __tablename__ = 'video_solutions'

    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True)
    problem_slug = Column(String)
    title = Column(String, nullable=False)
    description = Column(String)
    image = Column(String)
    url = Column(String)
    channel = Column(String)

    @classmethod
    def from_json(cls, data):
        return cls(
            uid=data.get('id'),
            problem_slug=data.get('problem_slug'),
            title=data.get('title'),
            description=data.get('description'),
            image=data.get('image'),
            url=data.get('url'),
            channel=data.get('channel')
        )

    def __response_json__(self):
        return {
            'id': self.uid,
            'problem_slug': self.problem_slug,
            'title': self.title,
            'description': self.description,
            'image': self.image,
            'url': self.url,
            'channel': self.channel
        }
