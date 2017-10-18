from flask import Blueprint
from . import views, errors
from ..models import Permission


main = Blueprint('main', __name__)


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
