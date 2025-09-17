import click
from flask import Flask
from app import create_app, db
from app.models import School, User, ROLE_HQ, ROLE_MANAGER, ROLE_STUDENT

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Create all tables (for local dev)."""
    with app.app_context():
        db.create_all()
        click.echo("Tables created.")

@app.cli.command("seed")
@click.option("--hq-email", default="hq@example.com")
@click.option("--manager-email", default="manager@example.com")
@click.option("--student-email", default="student@example.com")
@click.option("--password", default="Passw0rd!")
def seed(hq_email, manager_email, student_email, password):
    """Seed minimal data."""
    with app.app_context():
        s1 = School(name="A校舎")
        s2 = School(name="B校舎")
        db.session.add_all([s1, s2])
        db.session.flush()

        hq = User(email=hq_email, role=ROLE_HQ, school_id=None)
        hq.set_password(password)

        m = User(email=manager_email, role=ROLE_MANAGER, school_id=s1.id)
        m.set_password(password)

        st = User(email=student_email, role=ROLE_STUDENT, school_id=s1.id)
        st.set_password(password)

        db.session.add_all([hq, m, st])
        db.session.commit()
        click.echo(f"Seeded. Login: {hq_email}/{password}, {manager_email}/{password}, {student_email}/{password}")

if __name__ == "__main__":
    app.run()
