from wtforms import Form, StringField, validators


class GuideForm(Form):
    """
    Form for creating or editing a guide.
    """

    game_name = StringField(
        "Game Name", [validators.InputRequired(message="Game name is required.")]
    )
    title = StringField(
        "Title", [validators.InputRequired(message="Title is required.")]
    )
    content = StringField(
        "Content", [validators.InputRequired(message="Content is required.")]
    )
    link = StringField("Link", [validators.InputRequired(message="Link is required.")])
    video = StringField(
        "Video", [validators.InputRequired(message="Video URL is required.")]
    )
    image = StringField(
        "Image", [validators.InputRequired(message="Image URL is required.")]
    )


class GameForm(Form):
    """
    Form for creating or editing a game entry.
    """

    game_name = StringField(
        "Game Name", [validators.InputRequired(message="Game name is required.")]
    )
