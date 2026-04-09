from flask import Flask, request, render_template_string, redirect, url_for, flash, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import create_engine, text,cast,Date
from flask_migrate import Migrate
from datetime import datetime,timezone,date
import os
import uuid


#from flask import Flask, render_template, request, redirect, url_for, flash
#from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
#from werkzeug.security import check_password_hash


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


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(100), unique=True, nullable=False)


class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    Whrsh_Outlets_id = db.Column(db.Integer, nullable=False)  # just a plain field

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
    Wrhse_outlet_id = db.Column(db.Integer, nullable=False)  # just a plain field

    transaction_type = db.Column(db.String(50), nullable=False)
    good_crates = db.Column(db.Integer, default=0)
    worn_crates = db.Column(db.Integer, default=0)
    disposed_crates = db.Column(db.Integer, default=0)
    notes = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.now())
    staff_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<WarehouseTransaction {self.transaction_type} for Outlet {self.Wrhse_outlet_id}>"

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
#http://127.0.0.1:10000/init-db?token=changeme #to create all tables manually
@app.route("/init-db")
def init_db():
  token = request.args.get("token")
  if token != INIT_SECRET:
      return "Unauthorized", 403

  with app.app_context():
      db.create_all()
  return "Tables created successfully!"

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

  import subprocess

def connect_sqlalchemy_database_cmd():
    # Path to your psql.exe
    psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    
    # Full connection string
    conn_str = "postgresql://tgl_crates_db_user:Vk1PPiktlT6aktTgzdCCNkQZZFfLeiX5@dpg-d6uodkchg0os73f4kql0-a.oregon-postgres.render.com/tgl_crates_db"
    
    # Run the command
    subprocess.run([psql_path, conn_str])


@app.route("/github_instructions")
def github_instructions():
    return f"<pre>{github_upload_instructions()}</pre>"

## --- Routes ---
@app.route("/")
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
    print("total_collected_today",  total_collected_today)
    total_dispatched_today = total_daily_crates_dispatched()
    print("total_dispatched_today",  total_dispatched_today)
    recent_stcktake_crate = recent_wrhse_crates_stocktake_count()
    print("recent_stcktake_crate",  recent_stcktake_crate)
    total_available_for_use = recent_stcktake_crate - total_dispatched_today + total_collected_today
    print("total_available_for_use",  total_available_for_use)
    variance_today = total_collected_today - total_dispatched_today
    print("variance_today",  variance_today)
    denominator = recent_stcktake_crate
    print("denominator",  denominator)
    available_pct_today = (total_available_for_use / denominator * 100) if denominator > 0 else 0
    print("available_pct_today",  available_pct_today)

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
  print("DEBUG: usernames =", usernames)
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

@app.route("/dispatch", methods=["GET", "POST"])
def record_dispatch():
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

        staff_name = request.form.get("staff_name") or ""
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        new_warehouse_rcrd = WarehouseTransaction(
            Wrhse_outlet_id=warehouse_id,
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


@app.route("/collection", methods=["GET", "POST"])
def record_collection():
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

        staff_name = request.form.get("staff_name") or ""
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        new_warehouse_rcrd = WarehouseTransaction(
            Wrhse_outlet_id=warehouse_id,
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


@app.route("/dashboard_main")
def dashboard_main():
    # Ensure at least one warehouse exists
    warehouse = Warehouse.query.first()
    if not warehouse:
        warehouse = Warehouse(
            name="Tgl Warehouse",
            Whrsh_Outlets_id=1,
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

    # Outlets with transactions
    dispatched_outlets = db.session.query(WarehouseTransaction.Wrhse_outlet_id).distinct().all()
    outlet_ids = [id for (id,) in dispatched_outlets]
    outlet_names = db.session.query(Outlet.name).filter(Outlet.outlet_id.in_(outlet_ids)).all()
    all_outlets = [name for (name,) in outlet_names]

    # Build outlet stats
    outlet_stats = []
    for outlet_name in all_outlets:
        last_end_day = get_last_end_day_date()

        collected_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
            .filter(WarehouseTransaction.notes == outlet_name,
                    WarehouseTransaction.transaction_type == 'collection')
        dispatched_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
            .filter(WarehouseTransaction.notes == outlet_name,
                    WarehouseTransaction.transaction_type == 'dispatch')

        if last_end_day:
            collected_query = collected_query.filter(WarehouseTransaction.timestamp > last_end_day)
            dispatched_query = dispatched_query.filter(WarehouseTransaction.timestamp > last_end_day)

        collected = collected_query.scalar() or 0
        dispatched = dispatched_query.scalar() or 0

        recurrent_collected = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
            .filter(WarehouseTransaction.notes == outlet_name,
                    WarehouseTransaction.transaction_type == 'collection').scalar() or 0
        recurrent_dispatched = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
            .filter(WarehouseTransaction.notes == outlet_name,
                    WarehouseTransaction.transaction_type == 'dispatch').scalar() or 0

        recurrent_balance = recurrent_dispatched - recurrent_collected
        variance = dispatched - collected
        color = "table-danger" if variance > 0 else "table-success"

        outlet_stats.append({
            "name": outlet_name,
            "recurrent_balance": recurrent_balance,
            "dispatched": dispatched,
            "collected": collected,
            "variance": variance,
            "color": color
        })

    total_collected = total_daily_crates_collected()
    total_dispatched = total_daily_crates_dispatched()
    recent_stcktake_crate = recent_wrhse_crates_stocktake_count()

    total_available = recent_stcktake_crate - total_dispatched + total_collected
    variance = total_collected - total_dispatched
    denominator = recent_stcktake_crate
    available_pct = (total_available / denominator * 100) if denominator > 0 else 0

    warehouse_summary = {
        "name": warehouse.name,
        "last_stocktake": recent_stcktake_crate,
        "total_available": total_available,
        "total_dispatched": total_dispatched,
        "total_collected": total_collected,
        "variance": variance,
        "available_pct": round(available_pct, 2)
    }

    users = retrieve_offline_users()
    last_rec = EndDayLog.query.order_by(EndDayLog.created_at.desc()).first()
    reconciliations = EndDayLog.query.order_by(EndDayLog.created_at.desc()).limit(20).all()

    most_recent_stocktake = WarehouseTransaction.query\
        .filter_by(transaction_type="stocktake", Wrhse_outlet_id=1)\
        .order_by(WarehouseTransaction.timestamp.desc()).first()

    if most_recent_stocktake:
        last_stocktake_time = most_recent_stocktake.timestamp.strftime("%d %B %Y")
        warehouse_summary_text = f"Warehouse Summary Based On : Last Stocktake : <span style='color:blue;'>{last_stocktake_time}</span>"
    else:
        warehouse_summary_text = "<span style='color:red;'>Warehouse Summary : No stocktake transactions found</span>"

    rows = ""
    for outlet_name in all_outlets:
      """
      Calculate collected and dispatched crates for a given outlet
      since the last end day cutoff.
      """
      last_end_day = get_last_end_day_date()

      collected_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(
            WarehouseTransaction.notes == outlet_name,
            WarehouseTransaction.transaction_type == 'collection'
        )
      
      dispatched_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(
            WarehouseTransaction.notes == outlet_name,
            WarehouseTransaction.transaction_type == 'dispatch'
        )

      # Apply cutoff if it exists
      if last_end_day:
        collected_query = collected_query.filter(WarehouseTransaction.timestamp > last_end_day)
        dispatched_query = dispatched_query.filter(WarehouseTransaction.timestamp > last_end_day)

      collected = collected_query.scalar() or 0
      dispatched = dispatched_query.scalar() or 0
      
      # Recurrent balance: all-time (no cutoff filter)
      recurrent_collected = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
          .filter(
              WarehouseTransaction.notes == outlet_name,
              WarehouseTransaction.transaction_type == 'collection'
          ).scalar() or 0

      recurrent_dispatched = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
          .filter(
              WarehouseTransaction.notes == outlet_name,
              WarehouseTransaction.transaction_type == 'dispatch'
          ).scalar() or 0

      recurrent_balance = recurrent_dispatched - recurrent_collected

      variance = dispatched - collected
      color = "table-danger" if variance > 0 else "table-success"
      rows += f"<tr><td>{outlet_name}</td><td>{recurrent_balance}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"


    return render_template(
        "dashboard.html",
        warehouse=warehouse,
        rows=rows,
        warehouse_summary=warehouse_summary,
        warehouse_summary_text=warehouse_summary_text,
        outlet_stats=outlet_stats,
        users=users,
        last_rec=last_rec,
        reconciliations=reconciliations,
        app_auto_collections=total_collected,
        app_auto_dispatches=total_dispatched
    )

@app.route("/dashboard")
def dashboard():
    # Ensure at least one warehouse exists
    warehouse = Warehouse.query.first()
    if not warehouse:
        warehouse = Warehouse(
            name="Tgl Warehouse",
            Whrsh_Outlets_id=1,
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


    total_collected = total_daily_crates_collected()
    total_dispatched = total_daily_crates_dispatched()
    recent_stcktake_crate = recent_wrhse_crates_stocktake_count()

    total_available = recent_stcktake_crate - total_dispatched + total_collected
    variance = total_collected - total_dispatched
    denominator = recent_stcktake_crate
    available_pct = (total_available / denominator * 100) if denominator > 0 else 0

    warehouse_summary = {
        "name": warehouse.name,
        "last_stocktake": recent_stcktake_crate,
        "total_available": total_available,
        "total_dispatched": total_dispatched,
        "total_collected": total_collected,
        "variance": variance,
        "available_pct": round(available_pct, 2)
    }

    users = retrieve_offline_users()
    last_rec = EndDayLog.query.order_by(EndDayLog.created_at.desc()).first()
    reconciliations = EndDayLog.query.order_by(EndDayLog.created_at.desc()).limit(20).all()

    most_recent_stocktake = WarehouseTransaction.query\
        .filter_by(transaction_type="stocktake", Wrhse_outlet_id=1)\
        .order_by(WarehouseTransaction.timestamp.desc()).first()

    if most_recent_stocktake:
        last_stocktake_time = most_recent_stocktake.timestamp.strftime("%d %B %Y")
        warehouse_summary_text = f"Warehouse Summary Based On : Last Stocktake : <span style='color:blue;'>{last_stocktake_time}</span>"
    else:
        warehouse_summary_text = "<span style='color:red;'>Warehouse Summary : No stocktake transactions found</span>"

    rows = ""
    # Outlets with transactions
    dispatched_outlets = db.session.query(WarehouseTransaction.Wrhse_outlet_id).distinct().all()
    outlet_ids = [id for (id,) in dispatched_outlets]
    outlet_names = db.session.query(Outlet.name).filter(Outlet.outlet_id.in_(outlet_ids)).all()
    all_outlets = [name for (name,) in outlet_names]

    for outlet_name in all_outlets:

      #dispatched,collected,recurrent_balance,variance
      d, c, rb, v ,oid = get_daily_dispatch_vers_collection(outlet_name)
      collected = c
      dispatched = d
      
      # Recurrent balance: all-time (no cutoff filter)
      recurrent_balance = rb

      variance = v
      color = "table-danger" if variance > 0 else "table-success"
      rows += f"<tr><td>{outlet_name}</td><td>{recurrent_balance}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"


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
        app_auto_collections=total_collected,
        app_auto_dispatches=total_dispatched
    )

def get_daily_dispatch_vers_collection(outlet_name):
    #for outlet_name in all_outlets:
      """
      Calculate collected and dispatched crates for a given outlet
      since the last end day cutoff.
      """
      last_end_day = get_last_end_day_date()

      collected_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(
            WarehouseTransaction.notes == outlet_name,
            WarehouseTransaction.transaction_type == 'collection'
        )
      
      dispatched_query = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
        .filter(
            WarehouseTransaction.notes == outlet_name,
            WarehouseTransaction.transaction_type == 'dispatch'
        )

      # Apply cutoff if it exists
      if last_end_day:
        collected_query = collected_query.filter(WarehouseTransaction.timestamp > last_end_day)
        dispatched_query = dispatched_query.filter(WarehouseTransaction.timestamp > last_end_day)

      collected = collected_query.scalar() or 0
      dispatched = dispatched_query.scalar() or 0
      
      # Recurrent balance: all-time (no cutoff filter)
      recurrent_collected = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
          .filter(
              WarehouseTransaction.notes == outlet_name,
              WarehouseTransaction.transaction_type == 'collection'
          ).scalar() or 0

      recurrent_dispatched = db.session.query(db.func.sum(WarehouseTransaction.good_crates))\
          .filter(
              WarehouseTransaction.notes == outlet_name,
              WarehouseTransaction.transaction_type == 'dispatch'
          ).scalar() or 0

      outlet_id = db.session.query(db.func.max(WarehouseTransaction.Wrhse_outlet_id))\
          .filter(WarehouseTransaction.notes == outlet_name)\
          .scalar() or 0


      recurrent_balance = recurrent_dispatched - recurrent_collected

      variance = dispatched - collected
      print("dispathed" , dispatched,"collected",collected,"variance",variance)
      return dispatched,collected,recurrent_balance,variance,outlet_id


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

@app.route("/warehouse/<int:Whrsh_Outlets_id>/endday", methods=["POST"])
def endday(Whrsh_Outlets_id):
    warehouse = Warehouse.query.filter_by(Whrsh_Outlets_id=Whrsh_Outlets_id).first_or_404()

    dispatched_crates = request.form.get("app_dispatched")
    physical_crates = request.form.get("physical_crates")
    app_collections = request.form.get("app_collections")
    variance = request.form.get("variance")
    staff_name = request.form.get("staff_name")
    remarks = request.form.get("remarks")
    overwrite = request.form.get("overwrite")

    last_log = (
        EndDayLog.query
        .filter(cast(EndDayLog.created_at, Date) == date.today())
        .order_by(EndDayLog.created_at.desc())
        .first()
    )

    if last_log and not overwrite:
        new_values = {
            "dispatched_crates": dispatched_crates,
            "physical_crates": physical_crates,
            "app_collections": app_collections,
            "variance": variance,
            "staff_name": staff_name,
            "remarks": remarks
        }
        return jsonify({
            "status": "exists",
            "last_log": {
                "physical_crates": last_log.physical_crates,
                "app_collections": last_log.app_collections,
                "variance": last_log.variance,
                "staff_name": last_log.staff_name,
                "remarks": last_log.remarks
            },
            "new_values": new_values
        })

    # 1st preserve record for the uncollected outlets
    outlet_uncollected_carry_forward = []
    dispatched_outlets = db.session.query(WarehouseTransaction.Wrhse_outlet_id).distinct().all()
    outlet_ids = [id for (id,) in dispatched_outlets]
    outlet_names = db.session.query(Outlet.name).filter(Outlet.outlet_id.in_(outlet_ids)).all()
    all_outlets = [name for (name,) in outlet_names]

    for outlet_name in all_outlets:
        print("outlets name to auto add", outlet_name)
        d, c, rb, v, oid = get_daily_dispatch_vers_collection(outlet_name)

        if v > 0 and v != (d - c):
          continue


        new_warehouse_rcrd = WarehouseTransaction(
            Wrhse_outlet_id=oid,
            good_crates=v,
            worn_crates=0,
            disposed_crates=0,
            transaction_type="dispatch",
            notes=outlet_name,
            staff_name="Admin"
        )
        outlet_uncollected_carry_forward.append(new_warehouse_rcrd)

    # Insert or overwrite
    new_log = EndDayLog(
        warehouse_id=warehouse.Whrsh_Outlets_id,
        dispatched_crates=dispatched_crates,
        physical_crates=physical_crates,
        app_collections=app_collections,
        variance=variance,
        staff_name=staff_name,
        remarks=remarks
    )
    db.session.add(new_log)
    db.session.commit()

    if outlet_uncollected_carry_forward:
        db.session.add_all(outlet_uncollected_carry_forward)
        db.session.commit()

    return jsonify({"status": "updated", "message": "End of Day recorded successfully"})

@app.route("/Expire_Dwarehouse/<int:Whrsh_Outlets_id>/endday", methods=["POST"])
def endday_expired(Whrsh_Outlets_id):
    warehouse = Warehouse.query.filter_by(Whrsh_Outlets_id=Whrsh_Outlets_id).first_or_404()
    
    dispatched_crates = request.form.get("app_dispatched")
    physical_crates = request.form.get("physical_crates")
    app_collections = request.form.get("app_collections")
    variance = request.form.get("variance")
    staff_name = request.form.get("staff_name")
    remarks = request.form.get("remarks")
    overwrite = request.form.get("overwrite")

    last_log = (
    EndDayLog.query
    .filter(cast(EndDayLog.created_at, Date) == date.today())
    .order_by(EndDayLog.created_at.desc())
    .first()
    )

    if last_log and not overwrite:
        new_values = {
            "dispatched_crates":dispatched_crates,
            "physical_crates": physical_crates,
            "app_collections": app_collections,
            "variance": variance,
            "staff_name": staff_name,
            "remarks": remarks
        }
        return jsonify({
            "status": "exists",
            "last_log": {
                "physical_crates": last_log.physical_crates,
                "app_collections": last_log.app_collections,
                "variance": last_log.variance,
                "staff_name": last_log.staff_name,
                "remarks": last_log.remarks
            },
            "new_values": new_values
        })

    #1st preserve record for the uncollected outlets
    outlet_uncollected_carry_forward = []
    dispatched_outlets = db.session.query(WarehouseTransaction.Wrhse_outlet_id).distinct().all()
    outlet_ids = [id for (id,) in dispatched_outlets]
    outlet_names = db.session.query(Outlet.name).filter(Outlet.outlet_id.in_(outlet_ids)).all()
    all_outlets = [name for (name,) in outlet_names]

    for outlet_name in all_outlets:
      print("outlets name to auto add",outlet_name)
      #dispatched,collected,recurrent_balance,variance
      d, c, rb, v ,oid= get_daily_dispatch_vers_collection(outlet_name)
      collected = c
      dispatched = d
      
      # Recurrent balance: all-time (no cutoff filter)
      recurrent_balance = rb

      variance = v
      print(variance)
      #if variance >= 1:
      # Skip this outlet if variance <= 0
      if variance <= 0:
        continue

      new_warehouse_rcrd = WarehouseTransaction(
          Wrhse_outlet_id=oid,
          good_crates=variance,
          worn_crates=0,
          disposed_crates=0,
          transaction_type="dispatch",
          notes=outlet_name,
          staff_name="Admin"
      )
      outlet_uncollected_carry_forward.append(new_warehouse_rcrd)

        

    # Insert or overwrite
    new_log = EndDayLog(
        warehouse_id=warehouse.Whrsh_Outlets_id,   # <-- critical fix
        dispatched_crates=dispatched_crates,
        physical_crates=physical_crates,
        app_collections=app_collections,
        variance=variance,
        staff_name=staff_name,
        remarks=remarks
    )
    db.session.add(new_log)
    db.session.commit()
    
    for i in outlet_uncollected_carry_forward:
    
      db.session.add(i)
      db.session.commit()

    return jsonify({"status": "updated", "message": "End of Day recorded successfully"})

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
            .filter_by(transaction_type="stocktake", Wrhse_outlet_id=1)
            .order_by(WarehouseTransaction.timestamp.desc())
            .first()
        )

  if most_recent_stocktake:
      recent_stcktake_crate = most_recent_stocktake.good_crates
      print("Most recent stocktake good_crates for outlet 1001 =", recent_stcktake_crate)
  else:
      print("No stocktake transactions found for outlet 1001.")
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
@app.route('/warehouse/<int:Whrsh_Outlets_id>/stocktake', methods=['POST']) #Whrsh_Outlets_id
def warehouse_stocktake(Whrsh_Outlets_id):
  #def warehouse_stocktake(warehouse_id):
    #warehouse = Warehouse.query.get_or_404(warehouse_id)
    #print("DEBUG: Whrsh_Outlets_id =",Whrsh_Outlets_id)
    #warehouse_id = Warehouse.query.get_or_404(Whrsh_Outlets_id)

    #warehouse_id = Whrsh_Outlets_id
    warehouse_id = 1
    good_crates = int(request.form.get('good_crates', 0))
    worn_crates = int(request.form.get('worn_crates', 0))
    disposed_crates = int(request.form.get('disposed_crates', 0))
    transaction_type ="stocktake"
    #description = request.form.get('description', '')
    #ware_hse_name = warehouse_id
  
    # Query the Warehouse table where Whrsh_Outlets_id matches
    warehouse = Warehouse.query.filter_by(Whrsh_Outlets_id=warehouse_id).first()

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
    #  ,Whrsh_Outlets_id=warehouse_id
    #  ,good_crates=good_crates
    #  ,worn_crates=worn_crates
    #  ,disposed_crates=disposed_crates
    #  ,total_crates=good_crates + worn_crates)
    
    txn = WarehouseTransaction(
        Wrhse_outlet_id=warehouse_id,
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
def manage_users():
    create_message = ""
    update_message = ""
    delete_message = ""

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            name = request.form.get("name")
            existing_user = Users.query.filter_by(staff_name=name).first()
            if existing_user:
                create_message = f"User '{name}' already exists!"
            else:
                new_user = Users(staff_name=name)
                db.session.add(new_user)
                db.session.commit()
                create_message = f"User '{name}' added successfully!"

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