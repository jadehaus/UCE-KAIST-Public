# -*- encoding: utf-8 -*-
"""
Copyright (c) Minu Kim - minu.kim@kaist.ac.kr
Templates from AppSeed.us
"""

from app import app, db
from app.models import User, Department, Course


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Department': Department, 'Course': Course}


if __name__ == '__main__':
    app.run(use_reloader=False, debug=True)
