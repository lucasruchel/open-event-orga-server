from flask import g
from flask.ext.restplus import Resource, Namespace

from app.api.events import EVENT
from app.helpers.data import DataManager, record_activity
from app.helpers.data_getter import DataGetter
from app.models.role import Role
from app.models.user import User as UserModel, ATTENDEE
from app.models.user_detail import UserDetail as UserDetailModel
from app.models.users_events_roles import UsersEventsRoles
from app.api.helpers import custom_fields as fields
from app.api.helpers.helpers import requires_auth, can_access_account, staff_only
from app.api.helpers.utils import PAGINATED_MODEL, PaginatedResourceBase, BaseDAO, \
    PAGE_PARAMS, POST_RESPONSES, PUT_RESPONSES

api = Namespace('users', description='Users', path='/')

USER_DETAIL = api.model('UserDetail', {
    'firstname': fields.String(),
    'lastname': fields.String(),
    'details': fields.String(),
    'avatar': fields.Upload(),
    'contact': fields.String(),
    'facebook': fields.String(),
    'twitter': fields.String()
})

USER = api.model('User', {
    'id': fields.Integer(),
    'email': fields.Email(required=True),
    'signup_time': fields.DateTime(),
    'last_access_time': fields.DateTime(),
    'user_detail': fields.Nested(USER_DETAIL)
})

USER_PAGINATED = api.clone('UserPaginated', PAGINATED_MODEL, {
    'results': fields.List(fields.Nested(USER))
})

USER_PUT = api.clone('UserPut', USER)
del USER_PUT['id']
del USER_PUT['signup_time']
del USER_PUT['last_access_time']

USER_POST = api.model('UserPost', {
    'email': fields.Email(required=True),
    'password': fields.String(required=True)
})

# Responses

USER_POST_RESPONSES = POST_RESPONSES.copy()
del USER_POST_RESPONSES[404]
del USER_POST_RESPONSES[401]


# DAO

class UserDetailDAO(BaseDAO):
    pass


class UserDAO(BaseDAO):
    def create(self, data):
        data = self.validate(data)
        user = DataManager.create_user([data['email'], data['password']])
        return user

    def update(self, id_, data):
        data = self.validate_put(data, self.put_api_model)
        user_detail = data.get('user_detail', {})
        del data['user_detail']
        item = BaseDAO.update(self, id_, data, validate=False)
        DetailDAO.update(item.user_detail.id, user_detail)
        return item


DAO = UserDAO(UserModel, USER_POST, USER_PUT)
DetailDAO = UserDetailDAO(UserDetailModel, USER_DETAIL)


@api.route('/users/<int:user_id>')
@api.response(404, 'User not found')
class User(Resource):
    @requires_auth
    @can_access_account
    @api.doc('get_user')
    @api.marshal_with(USER)
    def get(self, user_id):
        """Fetch a user given its id"""
        return DAO.get(user_id)

    @requires_auth
    @can_access_account
    @api.doc('delete_user')
    @api.marshal_with(USER)
    def delete(self, user_id):
        """Delete a user given its id"""
        return DAO.delete(user_id)

    @requires_auth
    @can_access_account
    @api.doc('update_user', responses=PUT_RESPONSES)
    @api.marshal_with(USER)
    @api.expect(USER_PUT)
    def put(self, user_id):
        """Update a user given its id"""
        user = DAO.update(user_id, self.api.payload)
        record_activity('update_user', user=user)
        return user


@api.route('/users/me')
@api.response(404, 'User not found')
class UserSelf(Resource):
    @requires_auth
    @api.doc('get_self_user')
    @api.marshal_with(USER)
    def get(self):
        """Fetch the current authenticated user"""
        return getattr(g, 'user', None), 200


@api.route('/users/me/events')
@api.response(404, 'User not found')
class UserSelfEvents(Resource):
    @requires_auth
    @api.doc('get_self_events')
    @api.marshal_list_with(EVENT)
    def get(self):
        """Fetch the current authenticated user's events"""
        user = getattr(g, 'user', None)
        attendee_role = Role.query.filter_by(name=ATTENDEE).first()
        events = DataGetter.get_user_events(user_id=user.id).filter(UsersEventsRoles.role_id != attendee_role.id).all()
        return events, 200

@api.route('/users/me/tickets')
@api.response(404, 'User not found')
class UserSelfTickets(Resource):
    @requires_auth
    @can_access_account
    @api.doc('get_self_tickets')
    @api.marshal_list_with(EVENT)
    def get(self):
        """Fetch the current authenticated user's events"""
        user = getattr(g, 'user', None)
        attendee_role = Role.query.filter_by(name=ATTENDEE).first()
        events = DataGetter.get_user_events(user_id=user.id).filter(UsersEventsRoles.role_id != attendee_role.id).all()
        return events, 200

@api.route('/users')
class UserList(Resource):
    @requires_auth
    @staff_only
    @api.doc('list_users')
    @api.marshal_list_with(USER)
    def get(self):
        """List all users"""
        return DAO.list()

    @api.doc('create_user', responses=USER_POST_RESPONSES)
    @api.marshal_with(USER)
    @api.expect(USER_POST)
    def post(self):
        """Create a user"""
        return DAO.create(self.api.payload)


@api.route('/users/page')
class UserListPaginated(Resource, PaginatedResourceBase):
    @requires_auth
    @staff_only
    @api.doc('list_users_paginated', params=PAGE_PARAMS)
    @api.marshal_with(USER_PAGINATED)
    def get(self):
        """List users in a paginated manner"""
        args = self.parser.parse_args()
        return DAO.paginated_list(args=args)
