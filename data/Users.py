import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'Users'
    FIO = sqlalchemy.Column(sqlalchemy.String)
    Login = sqlalchemy.Column(sqlalchemy.String,
                           primary_key=True)
    h_password = sqlalchemy.Column(sqlalchemy.String)
    role = sqlalchemy.Column(sqlalchemy.String)
    status_str = sqlalchemy.Column(sqlalchemy.String)
    status_int = sqlalchemy.Column(sqlalchemy.Integer)
