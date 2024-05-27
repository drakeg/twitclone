from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class PollOptionForm(FlaskForm):
    option_text = StringField('Option', validators=[DataRequired(), Length(max=255)])

class PollForm(FlaskForm):
    question = StringField('Question', validators=[DataRequired(), Length(max=255)])
    options = FieldList(FormField(PollOptionForm), min_entries=2, max_entries=4, validators=[DataRequired()])
    duration_days = IntegerField('Days', validators=[NumberRange(min=0)], default=0)
    duration_hours = IntegerField('Hours', validators=[NumberRange(min=0, max=23)], default=0)
    duration_minutes = IntegerField('Minutes', validators=[NumberRange(min=0, max=59)], default=0)
    submit = SubmitField('Create Poll')