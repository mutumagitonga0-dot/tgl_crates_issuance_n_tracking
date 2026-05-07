import os
from datetime import datetime,timezone,date
from flask import Flask, request, render_template_string, redirect, url_for, flash, render_template, jsonify,json
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import create_engine, text,cast,Date,func,case
from flask_migrate import Migrate
#import uui
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


#from flask import Flask, render_template, request, redirect, url_for, flash
#from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
#from werkzeug.security import check_password_hash

#from flask import Blueprint, jsonify, request
#from sqlalchemy import func
#from yourapp.models import WarehouseTransactions, User, Branch
#from yourapp.extensions import db
#import subprocess

#bp = Blueprint("warehouse", __name__)

app = Flask(__name__)
app.secret_key = "super_secret_key"  # required for flash/session

# Secret token for init route (set in Render Environment tab)
INIT_SECRET = os.environ.get("INIT_SECRET", "changeme")

# Get DB URL from environment
db_url = os.environ.get("DATABASE_URL")

# Fallback for local dev
if not db_url:
  #db_url = "sqlite:///local.db"
  # Use SQL Server locally
  db_url = (
      "mssql+pyodbc:///?odbc_connect="
      "DRIVER={ODBC Driver 17 for SQL Server};"
      "SERVER=TOSHIBA\\SQLEXP2014;"
      "DATABASE=CrateTrackerDB;"
      "UID=sa;"
      "PWD=CMos@2019"
  )

# Fix Render’s default prefix if needed
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)


# External SQL Server connection
external_engine = create_engine(
    "mssql+pyodbc:///?odbc_connect="
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=tundagreen.aceplasticsafrica.com;"
    "DATABASE=ACELIVEDATA;"
    "UID=Usertunda;"
    "PWD=Tunda@2024"
)

# Apply config
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Import models AFTER db is defined
#import models
# --- Models ---
class Outlet(db.Model):
    __tablename__ = 'outlet'
    id = db.Column(db.Integer, primary_key=True)   # internal PK
    outlet_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, nullable=False)    


class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    whrsh_outlets_id = db.Column(db.Integer, nullable=False)  # just a plain field

    good_crates = db.Column(db.Integer, default=0)
    worn_crates = db.Column(db.Integer, default=0)
    disposed_crates = db.Column(db.Integer, default=0)
    dispatched_crates = db.Column(db.Integer, default=0)
    collected_crates = db.Column(db.Integer, default=0)
    total_crates = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Warehouse {self.name}>"


class WarehouseTransaction(db.Model):
    __tablename__ = 'warehouse_transactions'
    id = db.Column(db.Integer, primary_key=True)
    wrhse_outlet_id = db.Column(db.Integer, nullable=False)  # just a plain field

    transaction_type = db.Column(db.String(50), nullable=False)
    good_crates = db.Column(db.Integer, default=0)
    worn_crates = db.Column(db.Integer, default=0)
    disposed_crates = db.Column(db.Integer, default=0)
    notes = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.now())
    staff_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<WarehouseTransaction {self.transaction_type} for Outlet {self.wrhse_outlet_id}>"

class EndDayLog(db.Model):
    __tablename__ = "end_day_logs"

    id = db.Column(db.Integer, primary_key=True)
    #warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouse.id"), nullable=False)
    warehouse_id = db.Column(db.Integer, nullable=False) 
    dispatched_crates = db.Column(db.Integer, nullable=False)
    app_collections = db.Column(db.Integer, nullable=False)
    physical_crates = db.Column(db.Integer, nullable=False)
    variance = db.Column(db.Integer, nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    #warehouse = db.relationship("Warehouse", backref="end_day_logs")

# Secure one-time init route
# Example to create all tables manually: http://127.0.0.1:10000/init-db?token=changeme
@app.route("/init-db")
def init_db():
    token = request.args.get("token")
    if token != INIT_SECRET:
        return "Unauthorized", 403

    with app.app_context():
        # Ensure tables exist
        db.create_all()

        from sqlalchemy import text
        try:
            # Add username column with default if missing
            db.session.execute(text("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'username'
                )
                ALTER TABLE users ADD username NVARCHAR(80)
                CONSTRAINT DF_users_username DEFAULT 'tempuser' NOT NULL;
            """))

            # Add password_hash column with default if missing
            db.session.execute(text("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'password_hash'
                )
                ALTER TABLE users ADD password_hash NVARCHAR(200)
                CONSTRAINT DF_users_password_hash DEFAULT 'changeme' NOT NULL;
            """))

            # Add status column with default if missing
            db.session.execute(text("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'status'
                )
                ALTER TABLE users ADD status INT
                CONSTRAINT DF_users_status DEFAULT 1 NOT NULL;
            """))

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"Error altering table: {e}", 500

    return "Tables created and altered successfully!"

def run_enviroment_for_app_debbug():
    #1.cd C:\Users\Admin\crate-tracker\backend_for_web
    #2.venv\Scripts\Activate.ps1
    #3.python app.py or your app.py_name run
    print("terminal_process")

def push_to_github():
    #Nb.you should be here
    #(venv) PS C:\Users\Admin\crate-tracker\backend_for_web>

    # 1. Initialize Git in your project folder (only once)
    #git init

    # 2. Add your remote GitHub repository
    # Replace with your actual repo URL
    #git remote add origin https://github.com/your-username/your-repo.git
    #my correct path
    #git remote set-url origin https://github.com/mutumagitonga0-dot/tgl_crates_issuance_n_tracking.git"

    # 3. Stage all files (prepare them for commit)
    #git add .

    # 4. Commit your changes with a message
    #git commit -m "Initial commit or update backend code" 

    # 5. Push to GitHub
    # First push (sets branch name and upstream)
    #git branch -M main
    #git push -u origin main


    # upload any change Subsequent pushes (after making new changes)
    #git add .
    #git commit -m "Describe your changes here"
    #git push
    print("github_process")

def connect_sqlalchemy_database_through_cmd():
    # Path to your psql.exe
    psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    
    # Full connection string
    conn_str = "postgresql://tgl_crates_db_user:Vk1PPiktlT6aktTgzdCCNkQZZFfLeiX5@dpg-d6uodkchg0os73f4kql0-a.oregon-postgres.render.com/tgl_crates_db"
    
    # Run the command


    #if this error : ERROR:  character with byte sequence 0xe2 0x80 0x91 in encoding "UTF8" has no equivalent in encoding "WIN1252"
    #run this line \encoding UTF8
    
    # run this \x 
    # This shows each row with column names and values vertically. 

    #run \pset tuples_only off
    #That command tells psql to include column headers. If tuples_only is set to on, headers are hidden.

    #run  \x auto
    #This will switch between table and expanded view depending on row width, always showing headers.
    
    
    #subprocess.run([psql_path, conn_str])


@app.route("/github_instructions")
def github_instructions():
    return f"<pre>{github_upload_instructions()}</pre>"

## --- Routes ---
#@app.route("/", methods=["GET", "POST"])
#def login():
#    if request.method == "POST":
#        username = request.form["username"]
#        password = request.form["password"]
#        # Replace with proper authentication logic
#        if username == "admin" and password == "secret":
#            #return redirect(url_for("dashboard"))
#            return redirect(url_for("home"))
#        else:
#            flash("Invalid credentials, please try again.", "danger")
#    return render_template("login.html")

def update_user_password(username: str, plain_password: str) -> bool:
    """
    Hashes a plain password and updates the given user's record.
    Returns True if successful, False if user not found.
    """
    user = Users.query.filter_by(username=username).first()
    if not user:
        return False
    
    user.password_hash = generate_password_hash(plain_password)
    db.session.commit()
    return True

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #username = request.form["username"]
        username = request.form["username"].lower()
        password = request.form["password"]
        print(username,password)
        user = Users.query.filter_by(username=username).first()
        print(user)

        # Update Admin user
        #success = update_user_password("tempuser", "changeme")
        #if success:
        #    print("Password updated and hashed successfully.")
        #else:
        #    print("User not found.")
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            #print(generate_password_hash("1234"))
            flash("Invalid credentials, please try again.", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    # End the user session
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    outlets = Outlet.query.all()

    dispatched = (
        db.session.query(db.func.sum(WarehouseTransaction.good_crates))
        .filter(WarehouseTransaction.transaction_type == 'dispatch')
        .scalar()
    ) or 0

    collected = (
        db.session.query(db.func.sum(WarehouseTransaction.good_crates))
        .filter(WarehouseTransaction.transaction_type == 'collection')
        .scalar()
    ) or 0

    variance = dispatched - collected
    color = "table-danger" if variance > 0 else "table-success"

    warehouse_total = recent_wrhse_crates_stocktake_count()

    total_sent = dispatched
    total_received = collected
    current_balance = warehouse_total - total_sent + total_received


    total_collected_today = total_daily_crates_collected()
    #print("total_collected_today",  total_collected_today)
    total_dispatched_today = total_daily_crates_dispatched()
    #print("total_dispatched_today",  total_dispatched_today)
    recent_stcktake_crate = recent_wrhse_crates_stocktake_count()
    #print("recent_stcktake_crate",  recent_stcktake_crate)
    total_available_for_use = recent_stcktake_crate - total_dispatched_today + total_collected_today
    #print("total_available_for_use",  total_available_for_use)
    variance_today = total_collected_today - total_dispatched_today
    #print("variance_today",  variance_today)
    denominator = recent_stcktake_crate
    #print("denominator",  denominator)
    available_pct_today = (total_available_for_use / denominator * 100) if denominator > 0 else 0
    #print("available_pct_today",  available_pct_today)

    # Instead of building HTML here, just pass the values to the template
    return render_template(
        "home.html",
        warehouse_total=warehouse_total,
        current_balance=current_balance,
        total_available_for_use=total_available_for_use,
        total_sent=total_sent,
        total_dispatched_today=total_dispatched_today,
        total_received=total_received,
        total_collected_today=total_collected_today,
        variance=variance,
        variance_today=variance_today,
        available_pct_today=available_pct_today,
        outlets=outlets
    )


def retrieve_outlets():
    with external_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT [BranchName] FROM [Tunda Green Limited$Dimension2$69b6b001-139b-4a64-a385-4bc69d6bb6a5]"
        ))
        external_outlets = [row.BranchName for row in result]

    created_outlets = []  # will hold (id, name) pairs

    # Step 1: Add missing outlets
    for branch_name in external_outlets:
        existing = Outlet.query.filter_by(name=branch_name).first()
        if not existing:
            last_outlet = Outlet.query.order_by(Outlet.outlet_id.desc()).first()
            next_outlet_id = (last_outlet.outlet_id + 1) if last_outlet else 1000

            new_outlet = Outlet(
                name=branch_name,
                outlet_id=next_outlet_id
            )
            db.session.add(new_outlet)
            db.session.flush()
            created_outlets.append((new_outlet.outlet_id, new_outlet.name))

    # Step 2: Delete outlets that no longer exist externally
    for local_outlet in Outlet.query.all():
        if local_outlet.name not in external_outlets:
            db.session.delete(local_outlet)

    db.session.commit()

    # Step 3: Return synced outlets
    return [(o.outlet_id, o.name) for o in Outlet.query.all()]


def retrieve_outlets_manual_create():
    # Temporary hard-coded list for testing
    external_outlets = ['Katani', 'Airport', 'Mountain']

    created_outlets = []

    # Step 2: Sync Outlet table with these test names
    for branch_name in external_outlets:
        existing = Outlet.query.filter_by(name=branch_name).first()
        if not existing:
            last_outlet = Outlet.query.order_by(Outlet.outlet_id.desc()).first()
            next_outlet_id = (last_outlet.outlet_id + 1) if last_outlet else 1000

            new_outlet = Outlet(
                name=branch_name,
                outlet_id=next_outlet_id
            )
            db.session.add(new_outlet)
            db.session.flush()

            created_outlets.append((new_outlet.outlet_id, new_outlet.name))

    db.session.commit()

    # Step 3: Return both names and IDs
    return [(o.outlet_id, o.name) for o in Outlet.query.all()]


def populate_warehouses_with_active_outlets(created_outlets):
    for outlet_id, branch_name in created_outlets:
        existing_wh = Warehouse.query.filter_by(name=branch_name).first()
        if not existing_wh:
            new_wh = Warehouse(name=branch_name)
            db.session.add(new_wh)
            db.session.flush()
            print(f"Warehouse created with id {new_wh.id}, linked to outlet {outlet_id}")
    db.session.commit()


def retrieve_offline_users():
  users = Users.query.all()  # returns list of User objects
  usernames = [u.staff_name for u in users]  # extract usernames
  #print("DEBUG: usernames =", usernames)
  return usernames

def add_purchase(warehouse_id, crates, description=""):
    txn = WarehouseTransaction(
        warehouse_id=warehouse_id,
        transaction_type="purchase",
        crates=crates,
        description=description
    )
    warehouse = Warehouse.query.get(warehouse_id)
    if warehouse:
        warehouse.total_crates += crates
    db.session.add(txn)
    db.session.commit()

def record_loss(warehouse_id, crates, description="Damaged crates"):
    txn = WarehouseTransaction(
        warehouse_id=warehouse_id,
        transaction_type="loss",
        crates=-crates,
        description=description
    )
    warehouse = Warehouse.query.get(warehouse_id)
    if warehouse:
        warehouse.total_crates -= crates
    db.session.add(txn)
    db.session.commit()

@app.route("/record/<transaction_type>", methods=["GET", "POST"])
@login_required
def record_transaction(transaction_type):
    db.create_all()

    # FIX: properly unpack both id and name
    outlets = [(outlet_id, outlet_name) for outlet_id, outlet_name in retrieve_outlets()]
    users = retrieve_offline_users()
    staff_name = current_user.staff_name
    last_end_day = get_last_end_day_date()

    if request.method == "POST":
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        outlet_t = Outlet.query.filter_by(name=branchname).first()
        warehouse_id = outlet_t.outlet_id if outlet_t else None

        # --- Dispatch ---
        if transaction_type == "dispatch":
            good_crates = int(request.form.get("crates_sent") or 0)
            if good_crates <= 0 or not staff_name:
                flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
                return redirect(request.url)

            query = db.session.query(WarehouseTransaction).filter_by(
                wrhse_outlet_id=warehouse_id,
                good_crates=good_crates,
                worn_crates=0,
                disposed_crates=0,
                transaction_type="dispatch",
                notes=branchname,
                staff_name=staff_name
            )
            if last_end_day:
                query = query.filter(WarehouseTransaction.timestamp > last_end_day)

            if query.first():
                flash("⚠️ Duplicate dispatch record detected. Transaction discarded.", "warning")
                return redirect(request.url)

            db.session.add(WarehouseTransaction(
                wrhse_outlet_id=warehouse_id,
                good_crates=good_crates,
                worn_crates=0,
                disposed_crates=0,
                transaction_type="dispatch",
                notes=branchname,
                staff_name=staff_name
            ))
            db.session.commit()
            flash(f"Dispatch recorded: {good_crates} crates sent to {branchname} by {staff_name}.", "success")
            return redirect(url_for("dashboard"))

        # --- Collection ---
        elif transaction_type == "collection":
            good_crates = int(request.form.get("crates_collected") or 0)
            if good_crates <= 0 or not staff_name:
                flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
                return redirect(request.url)

            query = db.session.query(WarehouseTransaction).filter_by(
                wrhse_outlet_id=warehouse_id,
                good_crates=good_crates,
                worn_crates=0,
                disposed_crates=0,
                transaction_type="collection",
                notes=branchname,
                staff_name=staff_name
            )
            if last_end_day:
                query = query.filter(WarehouseTransaction.timestamp > last_end_day)

            if query.first():
                flash("⚠️ Duplicate collection record detected. Transaction discarded.", "warning")
                return redirect(request.url)

            db.session.add(WarehouseTransaction(
                wrhse_outlet_id=warehouse_id,
                good_crates=good_crates,
                worn_crates=0,
                disposed_crates=0,
                transaction_type="collection",
                notes=branchname,
                staff_name=staff_name
            ))
            db.session.commit()
            flash(f"Collection recorded: {good_crates} crates returned from {branchname} by {staff_name}.", "success")
            return redirect(url_for("dashboard"))

        # --- Multiple entries ---
        elif transaction_type == "multiple":
            completed_outlets = request.json or []  # Expect JSON payload

            for entry in completed_outlets:
                outlet_id = entry.get("outlet_id")
                outlet_name = entry.get("outlet_name")
                dispatched = int(entry.get("dispatched", 0))
                collected = int(entry.get("collected", 0))

                # Dispatch duplicate check
                if dispatched > 0:
                    query = db.session.query(WarehouseTransaction).filter_by(
                        wrhse_outlet_id=outlet_id,
                        good_crates=dispatched,
                        worn_crates=0,
                        disposed_crates=0,
                        transaction_type="dispatch",
                        notes=outlet_name,
                        staff_name=staff_name
                    )
                    if last_end_day:
                        query = query.filter(WarehouseTransaction.timestamp > last_end_day)

                    if query.first():
                        flash(f"⚠️ Duplicate dispatch record detected for {outlet_name}. Skipped.", "warning")
                    else:
                        db.session.add(WarehouseTransaction(
                            wrhse_outlet_id=outlet_id,
                            good_crates=dispatched,
                            worn_crates=0,
                            disposed_crates=0,
                            transaction_type="dispatch",
                            notes=outlet_name,
                            staff_name=staff_name
                        ))

                # Collection duplicate check
                if collected > 0:
                    query = db.session.query(WarehouseTransaction).filter_by(
                        wrhse_outlet_id=outlet_id,
                        good_crates=collected,
                        worn_crates=0,
                        disposed_crates=0,
                        transaction_type="collection",
                        notes=outlet_name,
                        staff_name=staff_name
                    )
                    if last_end_day:
                        query = query.filter(WarehouseTransaction.timestamp > last_end_day)

                    if query.first():
                        flash(f"⚠️ Duplicate collection record detected for {outlet_name}. Skipped.", "warning")
                    else:
                        db.session.add(WarehouseTransaction(
                            wrhse_outlet_id=outlet_id,
                            good_crates=collected,
                            worn_crates=0,
                            disposed_crates=0,
                            transaction_type="collection",
                            notes=outlet_name,
                            staff_name=staff_name
                        ))

            db.session.commit()
            flash("Multiple entries processed successfully.", "success")
            return redirect(url_for("dashboard"))

        else:
            flash("Invalid transaction type.", "danger")
            return redirect(request.url)

    # Render correct template
    if transaction_type == "multiple":
        return render_template("collections_dispatch_grid_per_row.html",
                               outlets=outlets, users=users, transaction_type=transaction_type)
    else:
        return render_template("record_entry_unified.html",
                               outlets=outlets, users=users, transaction_type=transaction_type)


@app.route("/backup/record/<transaction_type>", methods=["GET", "POST"])
@login_required
def backup_record_transaction(transaction_type):
    db.create_all()

    outlets = [name for name, name in retrieve_outlets()]
    users = retrieve_offline_users()

    if request.method == "POST":
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        outlet_t = Outlet.query.filter_by(name=branchname).first()
        warehouse_id = outlet_t.outlet_id if outlet_t else None

        # Determine transaction type based on which field is present
        if "crates_sent" in request.form:
            transaction_type = "dispatch"
            try:
                good_crates = int(request.form.get("crates_sent"))
            except (TypeError, ValueError):
                good_crates = 0
        elif "crates_collected" in request.form:
            transaction_type = "collection"
            try:
                good_crates = int(request.form.get("crates_collected"))
            except (TypeError, ValueError):
                good_crates = 0
        else:
            flash("Invalid submission: missing crates field.", "danger")
            return redirect(request.url)

        staff_name = current_user.staff_name
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Duplicate check
        last_end_day = get_last_end_day_date()
        query = db.session.query(WarehouseTransaction).filter_by(
            wrhse_outlet_id=warehouse_id,
            good_crates=good_crates,
            worn_crates=0,
            disposed_crates=0,
            transaction_type=transaction_type,
            notes=branchname,
            staff_name=staff_name
        )
        if last_end_day:
            query = query.filter(WarehouseTransaction.timestamp > last_end_day)

        existing = query.first()
        if existing:
            flash(f"⚠️ Duplicate {transaction_type} record detected. Transaction discarded.", "warning")
            return redirect(request.url)

        # Insert new record
        new_record = WarehouseTransaction(
            wrhse_outlet_id=warehouse_id,
            good_crates=good_crates,
            worn_crates=0,
            disposed_crates=0,
            transaction_type=transaction_type,
            notes=branchname,
            staff_name=staff_name
        )
        db.session.add(new_record)
        db.session.commit()

        flash(f"{transaction_type.capitalize()} recorded: {good_crates} crates for {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Render template, passing outlets and users
    return render_template("record_entry_unfied.html", outlets=outlets, users=users, transaction_type=transaction_type)

@app.route("/collections_dispatch", methods=["GET"])
def collections_dispatch():
    # Get all outlets
    outlets = retrieve_outlets()
    #dispatched =0
    #collected=0
    # Build summary list
    each_outlet_disp_collction_summ = []
    for outlet_id, outlet_name in outlets:
        #dispatched, collected = get_daily_dispatch_vers_collection(outlet_name)
        inv_response = get_inventory(outlet_name)
        inv_summary = inv_response.get_json()  # convert to dict

        dispatched = inv_summary.get("dispatched", 0)
        collected = inv_summary.get("collected", 0)

        each_outlet_disp_collction_summ.append({
            "outlet_id": outlet_id,
            "outlet_name": outlet_name,
            "dispatched": dispatched,
            "collected": collected
        })
    print(each_outlet_disp_collction_summ)

    #print(outlets)
    return render_template(
        "collections_dispatch_grid_per_row.html",
        #"collectionsDispatchForm.html",
        outlets=outlets,
        outlet_summ=each_outlet_disp_collction_summ
    )


@app.route("/not_unified_dispatch", methods=["GET", "POST"])
@login_required
def record_dispatch_not_unfied():
    db.create_all()

    # Step 1: Fetch branch names and users
    outlets = [name for name, name in retrieve_outlets()]
    users = retrieve_offline_users()

    if request.method == "POST":
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        outlet_t = Outlet.query.filter_by(name=branchname).first()
        warehouse_id = outlet_t.outlet_id if outlet_t else None

        try:
            good_crates = int(request.form.get("crates_sent"))
        except (TypeError, ValueError):
            good_crates = 0

        #staff_name = request.form.get("staff_name") or ""
        staff_name = current_user.staff_name  
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Define what makes a record "duplicate"
        #existing_query = db.session.query(WarehouseTransaction).filter_by(
        #    wrhse_outlet_id=warehouse_id,
        #    good_crates=good_crates,
        #    worn_crates=0,
        #    disposed_crates=0,
        #    transaction_type="dispatch",
        #    notes=branchname,
        #    #staff_name=staff_name
        #).first()

        last_end_day = get_last_end_day_date()
        # Build the query
        query = db.session.query(WarehouseTransaction).filter_by(
            wrhse_outlet_id=warehouse_id,
            good_crates=good_crates,
            worn_crates=0,
            disposed_crates=0,
            transaction_type="dispatch",
            notes=branchname,
            staff_name=staff_name
        )

        # Apply cutoff if needed
        if last_end_day:
            query = query.filter(WarehouseTransaction.timestamp > last_end_day)

        # Execute
        existing = query.first()

        if existing:
            # Duplicate found – discard and alert user
            flash("⚠️ Duplicate dispatch record detected. Transaction discarded.", "warning")
            return redirect(request.url)

        new_warehouse_rcrd = WarehouseTransaction(
            wrhse_outlet_id=warehouse_id,
            good_crates=good_crates,
            worn_crates=0,
            disposed_crates=0,
            transaction_type="dispatch",
            notes=branchname,
            staff_name=staff_name
        )
       
        db.session.add(new_warehouse_rcrd)
        db.session.commit()

        flash(f"Dispatch recorded: {good_crates} crates sent to {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Step 2: Render template, passing outlets and users
    return render_template("dispatch.html", outlets=outlets, users=users)

@app.route("/not_unified_collection", methods=["GET", "POST"])
@login_required
def record_collection_not_unfied():
    db.create_all()

    outlets = [name for name, name in retrieve_outlets()]
    users = retrieve_offline_users()

    if request.method == "POST":
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        outlet_t = Outlet.query.filter_by(name=branchname).first()
        warehouse_id = outlet_t.outlet_id if outlet_t else None

        try:
            good_crates = int(request.form.get("crates_collected"))
        except (TypeError, ValueError):
            good_crates = 0

        #staff_name = request.form.get("staff_name") or ""
        staff_name = current_user.staff_name  
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Define what makes a record "duplicate"
        #existing = db.session.query(WarehouseTransaction).filter_by(
        #    wrhse_outlet_id=warehouse_id,
        #    good_crates=good_crates,
        #    worn_crates=0,
        #    disposed_crates=0,
        #    transaction_type="collection",
        #    notes=branchname,
        #    #staff_name=staff_name
        #).first()

        last_end_day = get_last_end_day_date()
        # Build the query
        query = db.session.query(WarehouseTransaction).filter_by(
            wrhse_outlet_id=warehouse_id,
            good_crates=good_crates,
            worn_crates=0,
            disposed_crates=0,
            transaction_type="collection",
            notes=branchname,
            staff_name=staff_name
        )

        # Apply cutoff if needed
        if last_end_day:
            query = query.filter(WarehouseTransaction.timestamp > last_end_day)

        # Execute
        existing = query.first()

        if existing:
            # Duplicate found – discard and alert user
            flash("⚠️ Duplicate collection record detected. Transaction discarded.", "warning")
            return redirect(request.url)
        
        new_warehouse_rcrd = WarehouseTransaction(
            wrhse_outlet_id=warehouse_id,
            good_crates=good_crates,
            worn_crates=0,
            disposed_crates=0,
            transaction_type="collection",
            notes=branchname,
            staff_name=staff_name
        )
        db.session.add(new_warehouse_rcrd)
        db.session.commit()

        flash(f"Collection recorded: {good_crates} crates returned from {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Render template, passing outlets and users
    return render_template("collection.html", outlets=outlets, users=users)


@app.route("/outlet_grid")
def outlet_grid():
    return render_template("outlet_grid.html")

@app.route("/warehouse/add_entry", methods=["POST"])
def add_entry():
    data = request.get_json()
    outlet_id = data.get("outlet_id")
    dispatch_add = int(data.get("dispatch_add") or 0)
    collection_add = int(data.get("collection_add") or 0)

    outlet = Outlet.query.filter_by(id=outlet_id).first_or_404()

    outlet.total_dispatches = (outlet.total_dispatches or 0) + dispatch_add
    outlet.total_collections = (outlet.total_collections or 0) + collection_add

    db.session.commit()

    return jsonify({
        "status": "success",
        "outlet_id": outlet_id,
        "total_dispatches": outlet.total_dispatches,
        "total_collections": outlet.total_collections
    })


from itsdangerous import URLSafeTimedSerializer
serializer = URLSafeTimedSerializer(app.secret_key)
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        user = Users.query.filter_by(username=username).first()
        if user:
            token = serializer.dumps(user.id, salt="password-reset")
            reset_url = url_for("reset_password", token=token, _external=True)
            # TODO: send reset_url via email (Flask-Mail or SMTP)
            flash("Password reset link has been sent to your email.", "info")
        else:
            flash("User not found.", "danger")
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        user_id = serializer.loads(token, salt="password-reset", max_age=3600)
    except Exception:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("login"))

    user = Users.query.get(user_id)
    if request.method == "POST":
        new_password = request.form["password"]
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("Password updated successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/get_inventory/<outlet>")
def get_inventory(outlet):
    #from datetime import date
    # Example query: total dispatched + collected for today

    #dispatched,collected,recurrent_balance,variance
    d, c, rb, v ,oid,sn,fd,nd,thr_lt_d,thr_lt_c,outlts_summ = get_daily_dispatch_vers_collection(outlet)


    dispatched=d
    collected=c
    last_staff=sn
    recurrent_balance=rb
    variance=v
    outlet_id=oid
    night_forced=fd
    night_dispatch=nd
    thr_recent_dispatch=thr_lt_d
    thr_recent_collection=thr_lt_c

    #print("DEBUG dispatched:", dispatched, type(dispatched))
    #print("DEBUG collected:", collected, type(collected))
    #print("DEBUG recorded_by:", last_staff, type(last_staff))
    #print("DEBUG recurrent_balance:", recurrent_balance, type(recurrent_balance))
    #print("DEBUG variance:", variance, type(variance))
    #print("DEBUG outlet_id:", outlet_id, type(outlet_id))
    #print("DEBUG night_forced:", night_forced, type(night_forced))
    #print("DEBUG night_dispatch:", night_dispatch, type(night_dispatch))
    #print("DEBUG thr_recent_dispatch:", thr_recent_dispatch, type(thr_recent_dispatch))
    #if thr_recent_dispatch:
    #    print("DEBUG first dispatch entry:", thr_recent_dispatch[0], type(thr_recent_dispatch[0]))
    #print("DEBUG thr_recent_collection:", thr_recent_collection, type(thr_recent_collection))

    outlet_id = str(outlet_id) if outlet_id is not None else None
    night_forced = int(night_forced) if night_forced is not None else 0
    night_dispatch = int(night_dispatch) if night_dispatch is not None else 0

    # Ensure serialization
    #thr_recent_dispatch = [serialize_txn(txn) for txn in thr_recent_dispatch]
    #thr_recent_collection = [serialize_txn(txn) for txn in thr_recent_collection]

    payload = {
        "dispatched": dispatched,
        "collected": collected,
        "recorded_by": last_staff,
        "recurrent_balance": recurrent_balance,
        "variance": variance,
        "outlet_id": outlet_id,
        "night_forced": night_forced,
        "night_dispatch": night_dispatch,
        "thr_recent_dispatch": thr_recent_dispatch,
        "thr_recent_collection": thr_recent_collection
    }
    #print("DEBUG JSON string:", json.dumps(payload, indent=2))
    return jsonify(payload)
    #return {"dispatched": d, "collected": c, "recorded_by" :sn,"recent_dispatches": thr_lt_d,"recent_collections" :thr_lt_c}


@app.route("/warehouse/<int:warehouse_id>/collections_summary")
def collections_summary(warehouse_id):
    last_end_day = get_last_end_day_date()
    print(last_end_day)
    # Base query for per-user totals
    summary_query = (
        db.session.query(
        WarehouseTransaction.staff_name.label("staff_name"),
        func.sum(
            case(
                (WarehouseTransaction.transaction_type == 'dispatch', WarehouseTransaction.good_crates),
                else_=0
            )
        ).label("total_dispatches"),
        func.sum(
            case(
                (WarehouseTransaction.transaction_type == 'collection', WarehouseTransaction.good_crates),
                else_=0
            )
        ).label("total_collections"),

       (
        func.sum(
            case(
                (WarehouseTransaction.transaction_type == 'dispatch', WarehouseTransaction.good_crates),
                else_=0
            )
        )
        -
        func.sum(
            case(
                (WarehouseTransaction.transaction_type == 'collection', WarehouseTransaction.good_crates),
                else_=0
            )
        )
        ).label("total_variances")
        )
     #.filter(WarehouseTransaction.wrhse_outlet_id == warehouse_id)
        .group_by(WarehouseTransaction.staff_name)
    )
    print(summary_query)


    # Apply cutoff if available
    if last_end_day:
        summary_query = summary_query.filter(WarehouseTransaction.timestamp > last_end_day)

    summary = summary_query.all()
    print(summary)

    data = []
    for row in summary:
        # Branch breakdown for this user
        branch_query = (
            db.session.query(
                WarehouseTransaction.notes.label("branch"),
                func.sum(
                case(
                (WarehouseTransaction.transaction_type == 'collection', WarehouseTransaction.good_crates),
                else_=0
                )).label("collections"),
                func.sum(
                case(
                (WarehouseTransaction.transaction_type == 'dispatch', WarehouseTransaction.good_crates),
                else_=0
                )).label("dispatches"),
                (
                func.sum(
                case(
                    (WarehouseTransaction.transaction_type == 'dispatch', WarehouseTransaction.good_crates),
                    else_=0
                ))
                -
                func.sum(
                case(
                    (WarehouseTransaction.transaction_type == 'collection', WarehouseTransaction.good_crates),
                    else_=0
                ))
                ).label("variances")
                )
                .filter(
                WarehouseTransaction.staff_name == row.staff_name
                )
                .group_by(WarehouseTransaction.notes)
        )

        if last_end_day:
            branch_query = branch_query.filter(WarehouseTransaction.timestamp > last_end_day)

        branch_data = branch_query.all()

        data.append({
            "user": row.staff_name,
            "total_collections": row.total_collections or 0,
            "total_dispatches": row.total_dispatches or 0,
            "total_variances": row.total_variances or 0,
            "branches": [
                {
                    "branch": b.branch,
                    "collections": b.collections or 0,
                    "dispatches": b.dispatches or 0,
                    "variances": b.variances or 0
                }
                for b in branch_data
            ]
        })
        print(data)
    return jsonify(data)

#@app.route("/reconcile/<int:outlet_id>")
@app.route("/reconcile/<outlet_name>")
def reconcile_outlet(outlet_name):
    #dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=outlet_id).scalar() or 0
    #collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=outlet_id).scalar() or 0
    
    dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_name=outlet_name).scalar() or 0
    collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_name=outlet_name).scalar() or 0

    
    variance = dispatched - collected
    content = f"""
    <h2>Reconciliation for Outlet {outlet_name}</h2>
    <table class="table table-bordered">
      <tr><th>Dispatched</th><td>{dispatched}</td></tr>
      <tr><th>Collected</th><td>{collected}</td></tr>
      <tr class="table-{ 'danger' if variance>0 else 'success' }">
        <th>Variance</th><td>{variance}</td>
      </tr>
    </table>
    {home_button}
    """
    return render_template_string(layout, content=content)


@app.route("/reconciliation")
def reconciliation():
    #not in any use
    # Get the most recent EndDayLog entry
    last_log = (
        EndDayLog.query
        .order_by(EndDayLog.created_at.desc())
        .first()
    )

    # Wrap it in a list so the Jinja loop works
    reconciliations = [last_log] if last_log else []
    print("DEBUG: reconciliations =", reconciliations)

    return render_template("dashboard.html", reconciliations=reconciliations)

def get_last_end_day_date():
    last_log = (
        db.session.query(EndDayLog.created_at)
        .order_by(EndDayLog.created_at.desc())
        .first()
    )
    return last_log[0] if last_log else None

def total_daily_crates_dispatched():
    last_end_day = get_last_end_day_date()

    query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.transaction_type == 'dispatch')

    if last_end_day:
        query = query.filter(WarehouseTransaction.timestamp > last_end_day)

    total_dispatched = query.scalar() or 0
    return total_dispatched

def total_daily_crates_collected():
    last_end_day = get_last_end_day_date()

    query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
            .filter(WarehouseTransaction.transaction_type == 'collection')
    
    if last_end_day:
          query = query.filter(WarehouseTransaction.timestamp > last_end_day)

    total_collected = query.scalar() or 0
    return total_collected


@app.route("/dashboard")
@login_required
def dashboard():
    # Ensure at least one warehouse exists
    warehouse = Warehouse.query.first()
    if not warehouse:
        warehouse = Warehouse(
            name="Tgl Warehouse",
            whrsh_outlets_id=1,
            good_crates=0,
            worn_crates=0,
            disposed_crates=0,
            dispatched_crates=0,
            collected_crates=0,
            total_crates=0
        )
        db.session.add(warehouse)
        db.session.commit()
        flash("Default warehouse created: Tgl Warehouse", "info")


    total_collected_for_all = total_daily_crates_collected()
    total_dispatched_for_all = total_daily_crates_dispatched()
    recent_stcktake_crate = recent_wrhse_crates_stocktake_count()

    total_available = recent_stcktake_crate - total_dispatched_for_all + total_collected_for_all
    variance = total_collected_for_all - total_dispatched_for_all
    denominator = recent_stcktake_crate
    available_pct = (total_available / denominator * 100) if denominator > 0 else 0

    warehouse_summary = {
        "name": warehouse.name,
        "last_stocktake": recent_stcktake_crate,
        "total_available": total_available,
        "total_dispatched": total_dispatched_for_all,
        "total_collected": total_collected_for_all,
        "variance": variance,
        "available_pct": round(available_pct, 2)
    }

    users = retrieve_offline_users()
    last_rec = EndDayLog.query.order_by(EndDayLog.created_at.desc()).first()
    reconciliations = EndDayLog.query.order_by(EndDayLog.created_at.desc()).limit(20).all()

    most_recent_stocktake = WarehouseTransaction.query\
        .filter_by(transaction_type="stocktake", wrhse_outlet_id=1)\
        .order_by(WarehouseTransaction.timestamp.desc()).first()

    if most_recent_stocktake:
        last_stocktake_time = most_recent_stocktake.timestamp.strftime("%d %B %Y")
        warehouse_summary_text = f"Warehouse Summary Based On : Last Stocktake : <span style='color:blue;'>{last_stocktake_time}</span>"
    else:
        warehouse_summary_text = "<span style='color:red;'>Warehouse Summary : No stocktake transactions found</span>"

    rows = ""
    # Outlets with transactions
    dispatched_outlets = db.session.query(WarehouseTransaction.wrhse_outlet_id).distinct().all()
    outlet_ids = [id for (id,) in dispatched_outlets]
    outlet_names = db.session.query(Outlet.name).filter(Outlet.outlet_id.in_(outlet_ids)).all()
    all_outlets = [name for (name,) in outlet_names]

    for outlet_name in all_outlets:

      #dispatched,collected,recurrent_balance,variance
      d, c, rb, v ,oid,sn ,fd,nd,thr_lt_d,thr_lt_c,outlts_summ = get_daily_dispatch_vers_collection(outlet_name)
      collected = c
      total_dispatched = d
      # Recurrent balance: all-time (no cutoff filter)
      recurrent_balance = rb
      variance = v
      todays_dispatch = nd
      uncollected_yesterday = fd

      color = "table-danger" if variance > 0 else "table-success"
      rows += f"<tr><td>{outlet_name}</td><td>{recurrent_balance}</td><td>{uncollected_yesterday}</td><td>{todays_dispatch}</td><th>{total_dispatched}</th><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    #print("Warehouse object:", warehouse)
    #print("Warehouse.id:", warehouse.id if warehouse else None)
    #print("Warehouse.whrsh_outlets_id:", warehouse.whrsh_outlets_id if warehouse else None)

    return render_template(
        "dashboard.html",
        warehouse=warehouse,
        rows=rows,
        warehouse_summary=warehouse_summary,
        warehouse_summary_text=warehouse_summary_text,
        #outlet_stats=outlet_stats,
        users=users,
        last_rec=last_rec,
        reconciliations=reconciliations,
        app_auto_collections=total_collected_for_all,
        app_auto_dispatches=total_dispatched_for_all
    )

def get_all_outlets_collections_summary():
    """
    Loop through all outlets with collections > 0 since last cutoff
    and return their dispatch/collection summaries.
    """
    last_end_day = get_last_end_day_date()

    # Find all outlet names that had collections > 0 today
    outlets_with_collections = db.session.query(WarehouseTransaction.notes)\
        .filter(WarehouseTransaction.transaction_type == 'collection')

    if last_end_day:
        outlets_with_collections = outlets_with_collections.filter(WarehouseTransaction.timestamp > last_end_day)

    # Group by outlet name and only keep those with sum > 0
    outlets_with_collections = outlets_with_collections.group_by(WarehouseTransaction.notes)\
        .having(db.func.sum(WarehouseTransaction.good_crates) > 0).all()

    # Loop through each outlet and channel through your existing function
    summaries = []
    for outlet_row in outlets_with_collections:
        outlet_name = outlet_row[0]  # notes column
        data = get_daily_dispatch_vers_collection(outlet_name)
        summaries.append({
            "outlet_name": outlet_name,
            "summary": data
        })

    return summaries

@app.route("/get_user_collections_summary")
def get_user_collections_summary():
    summaries = get_all_outlets_collections_summary()
    return jsonify(summaries)

def get_daily_dispatch_vers_collection(outlet_name):
    """
    Calculate collected and dispatched crates for a given outlet
    since the last end day cutoff, plus recent records.
    """
    last_end_day = get_last_end_day_date()

    # Base queries
    last_staff_query =db.session.query(WarehouseTransaction.staff_name)\
        .filter(
        WarehouseTransaction.notes == outlet_name,
        WarehouseTransaction.transaction_type.in_(["collection", "dispatch"])
        )
    
    collected_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.notes == outlet_name,
                WarehouseTransaction.transaction_type == 'collection')

    dispatched_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.notes == outlet_name,
                WarehouseTransaction.transaction_type == 'dispatch')

    today_forced_dispatched_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.notes == outlet_name,
                WarehouseTransaction.transaction_type == 'dispatch',
                WarehouseTransaction.staff_name.like('System Auto%'))

    today_night_shift_dispatch_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.notes == outlet_name,
                WarehouseTransaction.transaction_type == 'dispatch',
                WarehouseTransaction.staff_name.notlike('System Auto%'))

    # Apply cutoff if it exists
    if last_end_day:
        collected_query = collected_query.filter(WarehouseTransaction.timestamp > last_end_day)
        dispatched_query = dispatched_query.filter(WarehouseTransaction.timestamp > last_end_day)
        today_forced_dispatched_query = today_forced_dispatched_query.filter(WarehouseTransaction.timestamp > last_end_day)
        today_night_shift_dispatch_query = today_night_shift_dispatch_query.filter(WarehouseTransaction.timestamp > last_end_day)
        last_staff_query =last_staff_query.filter(WarehouseTransaction.timestamp > last_end_day)
        
        # Recent dispatches (limit 5)
        thr_recent_dispatch = db.session.query(WarehouseTransaction)\
            .filter(WarehouseTransaction.notes == outlet_name,
                    WarehouseTransaction.transaction_type == 'dispatch',
                    WarehouseTransaction.timestamp > last_end_day)\
            .order_by(WarehouseTransaction.timestamp.desc())\
            .limit(3).all() #truck normally visit maximum of 2 per outlets

        # Recent collections (limit 5)
        thr_recent_collection = db.session.query(WarehouseTransaction)\
            .filter(WarehouseTransaction.notes == outlet_name,
                    WarehouseTransaction.transaction_type == 'collection',
                    WarehouseTransaction.timestamp > last_end_day)\
            .order_by(WarehouseTransaction.timestamp.desc())\
            .limit(3).all() #truck normally visit maximum of 2 per outlets
    else:
        thr_recent_dispatch = []
        thr_recent_collection = []

    # Convert to list of dicts
    thr_recent_dispatch = [serialize_txn(txn) for txn in thr_recent_dispatch]
    thr_recent_collection = [serialize_txn(txn) for txn in thr_recent_collection]
    #print(thr_recent_dispatch)
    # Scalars
    collected = collected_query.scalar() or 0
    dispatched = dispatched_query.scalar() or 0
    night_forced = today_forced_dispatched_query.scalar() or 0
    night_dispatch = today_night_shift_dispatch_query.scalar() or 0
    # Fetch the first row
    row = last_staff_query.first()
    last_staff = row[0] if row else None

    recurrent_collected = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.notes == outlet_name,
                WarehouseTransaction.transaction_type == 'collection').scalar() or 0

    recurrent_dispatched = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(WarehouseTransaction.notes == outlet_name,
                WarehouseTransaction.transaction_type == 'dispatch').scalar() or 0

    outlet_id = db.session.query(db.func.max(WarehouseTransaction.wrhse_outlet_id))\
        .filter(WarehouseTransaction.notes == outlet_name).scalar() or 0

    recurrent_balance = recurrent_dispatched - recurrent_collected
    variance = dispatched - collected

    # Build user collections summary
    user_collections_summary = {
        "user": last_staff,
        "total": collected,
        "collections": thr_recent_collection
    }
    #print("dispathed" , dispatched,"collected",collected,"variance",variance,"Recorded",last_staff,"forced_dispatch",night_forced,"normal_dispatch",night_dispatch,"thr_recent_dispatch",thr_recent_dispatch,"thr_recent_collection",thr_recent_collection)
    return dispatched,collected,recurrent_balance,variance,outlet_id,last_staff,night_forced,night_dispatch,thr_recent_dispatch,thr_recent_collection,user_collections_summary

def serialize_txn(txn):
    return {
        "timestamp": txn.timestamp.strftime("%Y-%m-%d %H:%M:%S") if txn.timestamp else None,
        "good_crates": txn.good_crates,
        "staff_name": txn.staff_name
    }

@app.route("/reconciliations/<int:offset>")
def get_reconciliations(offset=0):
    logs = (
        EndDayLog.query
        .order_by(EndDayLog.created_at.desc())
        .offset(offset)
        .limit(20)
        .all()
    )

    # Convert to JSON-friendly dicts
    data = []
    for rec in logs:
        data.append({
            "created_at": rec.created_at.strftime("%d %B %Y"),
            "dispatched_crates": rec.dispatched_crates,
            "app_collections": rec.app_collections,
            "physical_crates": rec.physical_crates,
            "staff_name": rec.staff_name,
            "variance": rec.variance,
            "performance": round(
                (rec.physical_crates / (rec.app_collections if rec.app_collections > 0 else 1)) * 100, 2
            )
        })
    return {"reconciliations": data}

@app.route("/warehouse/<int:id>/endday", methods=["POST"])
def endday(id):
    warehouse = Warehouse.query.filter_by(id=id).first_or_404()

    dispatched_crates = request.form.get("app_dispatched")
    physical_crates = request.form.get("physical_crates")
    app_collections = request.form.get("app_collections")
    variance = request.form.get("variance")
    staff_name = request.form.get("staff_name")
    remarks = request.form.get("remarks")
    overwrite = request.form.get("overwrite")
    new_end_day = request.form.get("new_end_day")

    payload = None  # ensure defined

    # Case 1: Force new entry
    if new_end_day:
        print("new_end_day logic detected")
        new_log = EndDayLog(
            warehouse_id=warehouse.whrsh_outlets_id,
            dispatched_crates=dispatched_crates,
            physical_crates=physical_crates,
            app_collections=app_collections,
            variance=variance,
            staff_name=staff_name,
            remarks=remarks
        )
        db.session.add(new_log)
        db.session.commit()
        payload = {"status": "inserted", "message": "New End of Day recorded successfully"}

    else:
        # Case 2: Check if today’s record exists
        last_log = (
            EndDayLog.query
            .filter(cast(EndDayLog.created_at, Date) == date.today())
            .order_by(EndDayLog.created_at.desc())
            .first()
        )

        if last_log:
            print("last_log detected")
            if overwrite:
                print("endday overwrite")
                # Overwrite existing record
                last_log.dispatched_crates = dispatched_crates
                last_log.physical_crates = physical_crates
                last_log.app_collections = app_collections
                last_log.variance = variance
                last_log.staff_name = staff_name
                last_log.remarks = remarks
                db.session.commit()
                payload = {"status": "updated", "message": "End of Day overwritten successfully"}
            else:
                # Return exists response with comparison
                new_values = {
                    "dispatched_crates": dispatched_crates,
                    "physical_crates": physical_crates,
                    "app_collections": app_collections,
                    "variance": variance,
                    "staff_name": staff_name,
                    "remarks": remarks
                }
                payload = {
                    "status": "exists",
                    "last_log": {
                        "physical_crates": last_log.physical_crates,
                        "app_collections": last_log.app_collections,
                        "variance": last_log.variance,
                        "staff_name": last_log.staff_name,
                        "remarks": last_log.remarks
                    },
                    "new_values": new_values
                }
        else:
            # Case 3: No record today, insert new
            new_log = EndDayLog(
                warehouse_id=warehouse.whrsh_outlets_id,
                dispatched_crates=dispatched_crates,
                physical_crates=physical_crates,
                app_collections=app_collections,
                variance=variance,
                staff_name=staff_name,
                remarks=remarks
            )
            db.session.add(new_log)
            db.session.commit()
            payload = {"status": "inserted", "message": "End of Day recorded successfully"}

    run_end_day_auto_reconcile_procedure()  # optional
    return jsonify(payload)

def run_end_day_auto_reconcile_procedure():
    print("runing auto end day closure")
    # Step 1: Get cutoff window (last two end_day_logs)
    recent_logs = db.session.query(EndDayLog.created_at)\
        .order_by(EndDayLog.created_at.desc())\
        .limit(2).all()
    if len(recent_logs) < 2:
        return []

    min_created_at = min(log.created_at for log in recent_logs)
    max_created_at = max(log.created_at for log in recent_logs)

    # Step 2: Aggregate dispatch/collection per outlet
    results = db.session.query(
        Outlet.name.label("outlet_name"),
        WarehouseTransaction.wrhse_outlet_id,
        func.sum(
            case((WarehouseTransaction.transaction_type == 'dispatch',
                  WarehouseTransaction.good_crates), else_=0)
        ).label("total_dispatch"),
        func.sum(
            case((WarehouseTransaction.transaction_type == 'collection',
                  WarehouseTransaction.good_crates), else_=0)
        ).label("total_collection")
    ).join(Outlet, Outlet.outlet_id == WarehouseTransaction.wrhse_outlet_id)\
     .filter(WarehouseTransaction.timestamp.between(min_created_at, max_created_at))\
     .group_by(Outlet.name, WarehouseTransaction.wrhse_outlet_id)\
     .order_by(Outlet.name).all()

    summary = []
    # Step 3: Apply rules per outlet
    for row in results:
        variance = (row.total_dispatch or 0) - (row.total_collection or 0)
        action_taken = "No variance"

        if variance > 0:
            if (row.total_collection or 0) == 0:
                # Case A: No collection → zero out previous dispatch and add new transaction
                latest_dispatch = db.session.query(WarehouseTransaction)\
                    .filter(WarehouseTransaction.wrhse_outlet_id == row.wrhse_outlet_id,
                            WarehouseTransaction.transaction_type == 'dispatch')\
                    .order_by(WarehouseTransaction.timestamp.desc()).first()

                if latest_dispatch:
                    # Zero out the previous dispatch
                    latest_dispatch.good_crates = 0
                    db.session.commit()

                    # Create a new transaction to carry variance forward
                    new_tx = WarehouseTransaction(
                        wrhse_outlet_id=row.wrhse_outlet_id,
                        transaction_type='dispatch',
                        good_crates=variance,
                        notes=row.outlet_name,
                        timestamp=datetime.now(),
                        staff_name="System Auto‑CarryForward"
                    )
                    db.session.add(new_tx)
                    db.session.commit()

                action_taken = "Created new transaction and zeroed previous dispatch"

            elif (row.total_collection or 0) > 0:
                # Case B: Partial collection → adjust dispatch and create new entry
                latest_dispatch = db.session.query(WarehouseTransaction)\
                    .filter(WarehouseTransaction.wrhse_outlet_id == row.wrhse_outlet_id,
                            WarehouseTransaction.transaction_type == 'dispatch')\
                    .order_by(WarehouseTransaction.timestamp.desc()).first()

                if latest_dispatch:
                    latest_dispatch.good_crates -= variance
                    db.session.commit()

                    new_tx = WarehouseTransaction(
                        wrhse_outlet_id=row.wrhse_outlet_id,
                        transaction_type='dispatch',
                        good_crates=variance,
                        notes=row.outlet_name,
                        timestamp=datetime.now(),
                        staff_name="System Auto‑Adjust"
                    )
                    db.session.add(new_tx)
                    db.session.commit()
                action_taken = "Adjusted dispatch and created new entry"

        summary.append({
            "outlet_name": row.outlet_name,
            "wrhse_outlet_id": row.wrhse_outlet_id,
            "total_dispatch": row.total_dispatch or 0,
            "total_collection": row.total_collection or 0,
            "variance": variance,
            "action_taken": action_taken
        })
    #print(summary)
    # Step 4: Export summary to PDF
    export_summary_to_pdf(summary)

    return summary


def export_summary_to_pdf(summary):
    filename = f"end_day_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Crate Tracker - End Day Summary Report")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Table-like output
    y = height - 100
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Outlet")
    c.drawString(200, y, "Dispatch")
    c.drawString(280, y, "Collection")
    c.drawString(370, y, "Variance")
    c.drawString(450, y, "Action Taken")
    y -= 20

    c.setFont("Helvetica", 10)
    for row in summary:
        c.drawString(50, y, row['outlet_name'])
        c.drawString(200, y, str(row['total_dispatch']))
        c.drawString(280, y, str(row['total_collection']))
        c.drawString(370, y, str(row['variance']))
        c.drawString(450, y, row['action_taken'])
        y -= 20
        if y < 100:  # new page if needed
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

    # Footer with signature line
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 80, "System generated by Crate Tracker")
    c.line(50, 60, 250, 60)
    c.drawString(50, 50, "Manager Signature")

    c.save()
    print(f"Summary PDF generated: {filename}")

@app.route("/app_auto_collections")
def get_app_collections():
    # Example: calculate from EndDayLog or Warehouse
    latest_value = db.session.query(db.func.sum(EndDayLog.app_collections)).scalar() or 0
    print("DEBUG: app_collections =", latest_value) 
    return {"app_collections": latest_value}

@app.route("/app_auto_dispatches")
def get_app_dispatches():
    # Example: calculate from EndDayLog or Warehouse
    #latest_value = db.session.query(db.func.sum(EndDayLog.app_collections)).scalar() or 0
    latest_value =total_daily_crates_dispatched()
    print("DEBUG: app_dispatched =", latest_value) 
    return {"app_dispatched": latest_value}


@app.route("/warehouse/<int:warehouse_id>")
def warehouse_detail(warehouse_id):
  warehouse ={"id": warehouse_id, "name": "Main Warehouse", "collection_total": 10}
  rows_html = "<tr><td>Outlet A</td><td>20</td><td>15</td><td>5</td></tr>"
  return render_template("warehouse.html", warehouse=warehouse, rows=rows_html)


def recent_wrhse_crates_stocktake_count():
  recent_stcktake_crate=0

  most_recent_stocktake = (
            WarehouseTransaction.query
            .filter_by(transaction_type="stocktake", wrhse_outlet_id=1)
            .order_by(WarehouseTransaction.timestamp.desc())
            .first()
        )

  if most_recent_stocktake:
      recent_stcktake_crate = most_recent_stocktake.good_crates
      #print("Most recent stocktake good_crates for outlet 1001 =", recent_stcktake_crate)
  #else:
  #    print("No stocktake transactions found for outlet 1001.")
  return recent_stcktake_crate       

def validate_staff_selection(field_name="staff_name"):
    """
    Validate that the submitted staff_name exists in the User table.
    Returns None if valid, or a redirect response if invalid.
    """
    staff_name = request.form.get(field_name)

    # Blank check
    if not staff_name:
        flash("Please select an existing staff member.")
        return redirect(request.url)

    # Existence check
    user_exists = db.session.query(Users).filter_by(staff_name=staff_name).first()
    if not user_exists:
        flash(f"User '{staff_name}' does not exist. Please choose a valid staff member.")
        return redirect(request.url)

    # Valid → continue
    return None

#@app.route('/warehouse/<int:warehouse_id>/stocktake', methods=['POST'])
@app.route('/warehouse/<int:whrsh_outlets_id>/stocktake', methods=['POST']) #whrsh_outlets_id
def warehouse_stocktake(whrsh_outlets_id):
  #def warehouse_stocktake(warehouse_id):
    #warehouse = Warehouse.query.get_or_404(warehouse_id)
    #print("DEBUG: whrsh_outlets_id =",whrsh_outlets_id)
    #warehouse_id = Warehouse.query.get_or_404(whrsh_outlets_id)

    #warehouse_id = whrsh_outlets_id
    warehouse_id = 1
    good_crates = int(request.form.get('good_crates', 0))
    worn_crates = int(request.form.get('worn_crates', 0))
    disposed_crates = int(request.form.get('disposed_crates', 0))
    transaction_type ="stocktake"
    #description = request.form.get('description', '')
    #ware_hse_name = warehouse_id
  
    # Query the Warehouse table where whrsh_outlets_id matches
    warehouse = Warehouse.query.filter_by(whrsh_outlets_id=warehouse_id).first()

    if warehouse:
        ware_hse_name = warehouse.name
        print("DEBUG: warehsename =", ware_hse_name)
    else:
        print("No warehouse found for outlet_id =", warehouse_id)
        print("DEBUG: warehsename =", ware_hse_name)

    staff_name=request.form.get('staff_name', '')
    #warehouse.good_crates = good_crates
    #warehouse.worn_crates = worn_crates
    #warehouse.disposed_crates = disposed_crates
    #warehouse.total_crates = good_crates + worn_crates
    #print("DEBUG: transaction_type =", transaction_type)
    # Call the reusable validator
    validation = validate_staff_selection()
    if validation:  # If it returned a redirect, stop here
        return validation
    
    #print("DEBUG: branchname =", warehouse_id)
    #warehouse_id=warehouse.id,
    #txn = Warehouse(name=""
    #  ,whrsh_outlets_id=warehouse_id
    #  ,good_crates=good_crates
    #  ,worn_crates=worn_crates
    #  ,disposed_crates=disposed_crates
    #  ,total_crates=good_crates + worn_crates)
    
    txn = WarehouseTransaction(
        wrhse_outlet_id=warehouse_id,
        good_crates=good_crates + worn_crates,
        worn_crates=worn_crates,
        disposed_crates=disposed_crates,
        transaction_type=transaction_type,
       notes = ware_hse_name,
        staff_name=staff_name
    )

    db.session.add(txn)
    db.session.commit()

    flash("Stocktake updated successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route("/manage_users", methods=["GET", "POST"])
@login_required
def manage_users():
    create_message = ""
    update_message = ""
    delete_message = ""

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            name = request.form.get("name")
            plain_password = request.form.get("password")  # new field from form
            existing_user = Users.query.filter_by(staff_name=name).first()

            if existing_user:
                create_message = f"User '{name}' already exists!"
            else:
                # Hash the admin-provided password
                hashed_pw = generate_password_hash(plain_password)

                new_user = Users(
                    staff_name=name,
                    username=name,  # you can adjust if you want username separate
                    password_hash=hashed_pw,
                    status=1
                )
                db.session.add(new_user)
                db.session.commit()
                create_message = f"User '{name}' added successfully with initial password!"

        elif action == "update":
            user_id = request.form.get("username")
            new_name = request.form.get("new_name")
            if not new_name:
                update_message = "New name is required."
            else:
                user = Users.query.get(user_id)
                if user:
                    oldname = user.staff_name
                    user.staff_name = new_name
                    db.session.commit()
                    update_message = f"User '{oldname}' updated to '{new_name}' successfully!"
                else:
                    update_message = "User not found."

        elif action == "delete":
            user_id = request.form.get("del_username")
            user = Users.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                delete_message = f"User '{user.staff_name}' deleted successfully!"
            else:
                delete_message = "User not found."

    users = Users.query.all()

    return render_template(
        "manage_users.html",
        users=users,
        create_message=create_message,
        update_message=update_message,
        delete_message=delete_message
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT
    app.run(host="0.0.0.0", port=port, debug=True)