from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema, Relationship

from app.api.helpers.utilities import dasherize


class EventTypeSchema(Schema):
    """
    Api Schema for event type model
    """

    class Meta:
        """
        Meta class for event type Api Schema
        """
        type_ = 'event-type'
        self_view = 'v1.event_type_detail'
        self_view_kwargs = {'id': '<id>'}
        inflect = dasherize

    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    slug = fields.Str(dump_only=True)
    events = Relationship(attribute='event',
                          self_view='v1.event_type_event',
                          self_view_kwargs={'id': '<id>'},
                          related_view='v1.event_list',
                          related_view_kwargs={'event_type_id': '<id>'},
                          many=True,
                          schema='EventSchema',
                          type_='event')
