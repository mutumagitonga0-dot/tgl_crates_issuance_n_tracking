from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import create_engine, text
from datetime import datetime,timezone
from flask import redirect, url_for, flash
import os
import uuid


app = Flask(__name__)
app.secret_key = "super_secret_key"  # required for flash/session


db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres123@localhost:5432/CrateTrackerDB"
)


app.config['SQLALCHEMY_DATABASE_URI'] = db_url
db = SQLAlchemy(app)


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

# --- Layout Template with Navbar ---
layout = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Crate Tracker</title>
  <!-- Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

  <!-- Navigation Bar -->
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">📦 Crate Tracker</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
          <li class="nav-item"><a class="nav-link" href="/dashboard">Dashboard</a></li>
          <li class="nav-item"><a class="nav-link" href="/dispatch">Dispatch</a></li>
          <li class="nav-item"><a class="nav-link" href="/collect">Collection</a></li>
          <li class="nav-item"><a class="nav-link" href="/manage_users">Manage Users</a></li>
        </ul>
      </div>
    </div>
  </nav>

  <div class="container mt-4">

    <!-- Flash messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {{ content|safe }}

  </div>

  <!-- Footer -->
  <footer class="bg-light text-center text-muted py-3 mt-4 border-top">
    <small>&copy; 2026 Crate Tracker | Designed for operational excellence</small>
  </footer>

  <!-- Bootstrap JS Bundle (needed for modal, navbar, alerts) -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --- Reusable Home Button ---
home_button = "<a href='/' class='btn btn-secondary mt-3'>⬅️ Return to Home</a>"

# --- Routes ---
@app.route("/")
def home():
    # Step 1: Get distinct outlet names from Dispatch table
    #distinct_outlets = db.session.query(Dispatch.outlet_name).distinct().all()

    # Step 2: Insert them into Outlet table if not already present
    #for (outlet_name,) in distinct_outlets:
    #    if outlet_name:  # skip nulls
    #        existing = Outlet.query.filter_by(name=outlet_name).first()
    #        if not existing:
    #            new_outlet = Outlet(name=outlet_name)
    #            db.session.add(new_outlet)

    #db.session.commit()

    #outlets = Outlet.query.all()
    rows = ""

    #outlts=retrieve_outlets()
    #print("outlets fecthed",  outlts)
    #outlets = [id for id, _ in outlts]
    
    #print("DEBUG: outlets =",  outlets)
    outlets = Outlet.query.all()
    #for o in outlets:
  
    #dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=o.id).scalar() or 0
    #dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_name=o.id).scalar() or 0
    #collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=o.id).scalar() or 0
    #collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_name=o.id).scalar() or 0
    
    # Example: total dispatched crates for a given outlet
    #dispatched = (
    #    db.session.query(db.func.sum(WarehouseTransaction.good_crates))
    #    .filter_by(warehouse_id=outlets.id, transaction_type='dispatch')
    #    .scalar()
    #) or 0
    dispatched = (
        db.session.query(db.func.sum(WarehouseTransaction.good_crates))
        .filter(WarehouseTransaction.transaction_type == 'dispatch')
        .scalar()
    ) or 0
    print("total dispacthed",  dispatched)
  
    # Example: total collected crates for the same outlet
    #collected = (
    #    db.session.query(db.func.sum(WarehouseTransaction.good_crates))
    #    .filter_by(warehouse_id=outlets.id, transaction_type='collection')
    #    .scalar()
    #) or 0
    collected = (
    db.session.query(db.func.sum(WarehouseTransaction.good_crates))
    .filter(WarehouseTransaction.transaction_type == 'collection')
    .scalar()
    ) or 0

    print("total collected",  collected)
    
    variance = dispatched - collected
    color = "table-danger" if variance > 0 else "table-success"
    #rows += f"<tr><td>{o.name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"
    rows += f"<tr><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    #summary_table = f"""
    ##<h2>Outlet Summary</h2>
    #<table class="table table-bordered">
    #  <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
    #  <tbody>{rows}</tbody>
    #</table>
    #"""

    # Warehouse total crates (assuming you track in Warehouse table)
    #warehouse_total = db.session.query(db.func.sum(Warehouse.crates)).scalar() or 0
    #warehouse_total = db.session.query(db.func.sum(Warehouse.total_crates)).scalar() or 0
    #warehouse = Warehouse.query.first()  # adjust if multiple warehouses

    warehouse_total= recent_wrhse_crates_stocktake_count()



    # Total dispatched to outlets
    #total_sent = db.session.query(db.func.sum(Dispatch.crates_sent)).scalar() or 0
    total_sent = dispatched

    # Total collected back from outlets
    #total_received = db.session.query(db.func.sum(Collection.crates_collected)).scalar() or 0
    total_received =  collected

    # Variance between sent and received
    #variance = total_sent - total_received

    # Current warehouse balance (original stock - sent + received)
    current_balance = warehouse_total - total_sent + total_received
    summary_table = f"""
    <div class="border p-3 mb-3 rounded bg-info bg-opacity-25">
      <h4 class="text-center">📊 Main Warehouse Summary</h4>
      <table class="table table-bordered table-striped">
        <thead class="table-light">
          <tr>
            <th>Metric</th>
            <th>Crates</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Total Crates Confirmed on last Stocktake</td>
            <td>{warehouse_total}</td>
          </tr>
          <tr class="table-success">
            <td>Current Warehouse Balance</td>
            <td>{current_balance}</td>
          </tr>
          <tr>
            <td>Total Issued to Outlets</td>
            <td>{total_sent}</td>
          </tr>
          <tr>
            <td>Total Received Back</td>
            <td>{total_received}</td>
          </tr>
          <tr class="table-warning">
            <td>Variance (Issued - Received)</td>
            <td>{variance}</td>
          </tr>
          
        </tbody>
      </table>
    </div>
    """


    shortcuts = """
    <div class="d-grid gap-3 mb-4">
      <a href="/dispatch" class="btn btn-success btn-lg">➕ Record Dispatch</a>
      <a href="/collect" class="btn btn-warning btn-lg">📥 Record Collection</a>
      <a href="/dashboard" class="btn btn-primary btn-lg">📋 View All Outlets Dashboard</a>
      <!--a href="/reconcile/1" class="btn btn-info btn-lg">📊 Reconcile Outlet 1</a-->
      <!--a href="/manage_users" class="btn btn-dark btn-lg">🏬 Manage Users</a-->
    </div>
    """

    content = shortcuts + summary_table
    return render_template_string(layout, content=content)

def retrieve_outlets():
    with external_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT [BranchName] FROM [Tunda Green Limited$Dimension2$69b6b001-139b-4a64-a385-4bc69d6bb6a5]"
        ))
        external_outlets = [row.BranchName for row in result]

    created_outlets = []  # will hold (id, name) pairs

    # Step 2: Sync Outlet table
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
          db.session.flush()  # ensures new_outlet.id is available

          created_outlets.append((new_outlet.outlet_id, new_outlet.name))
    db.session.commit()

    # Step 3: Populate warehouses with active outlets
    #populate_warehouses_with_active_outlets(created_outlets) 

    # Step 4: Return both names and IDs
    return [(o.outlet_id, o.name) for o in Outlet.query.all()]
    #return [o.name for o in Outlet.query.all()]


def populate_warehouses_with_active_outlets(created_outlets):
    for outlet_id, branch_name in created_outlets:
        existing_wh = Warehouse.query.filter_by(name=branch_name).first()
        if not existing_wh:
            new_wh = Warehouse(name=branch_name)
            db.session.add(new_wh)
            db.session.flush()
            print(f"Warehouse created with id {new_wh.id}, linked to outlet {outlet_id}")
    db.session.commit()


def retrieve_outlets_No_external_Id():
    # Step 1: Fetch branch names from external DB
    with external_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT [BranchName], [DimensionValueID] "
            "FROM [Tunda Green Limited$Dimension2$69b6b001-139b-4a64-a385-4bc69d6bb6a5]"
        ))
        external_outlets = [(row.BranchName, row.DimensionValueID) for row in result]

    # Step 2: Sync with local Outlet table
    for branch_name, external_id in external_outlets:
        existing = Outlet.query.filter_by(outlet_id=external_id).first()
        if not existing:
            new_outlet = Outlet(name=branch_name, outlet_id=external_id)
            db.session.add(new_outlet)
    db.session.commit()

    # Step 3: Return the full list from local DB
    return [o.name for o in Outlet.query.all()]


def retrieve_users_external():
  with db.engine.connect() as conn:
    result = conn.execute(text("SELECT username FROM users"))
    users = [row.staff_name for row in result]
  return users

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
    # At app startup, or before you insert
    db.create_all()
    # Step 1: Fetch branch names from external DB or helper
    outlets = retrieve_outlets()
    
    outlets = [name for name, name in outlets]
    #outlets = [id for id, _ in outlets]
    #print("DEBUG: usernames =", outlets)
    
    Users = retrieve_offline_users()

    # Step 2: Build the form HTML dynamically
    options_html = "".join([f'<option value="{o}">{o}</option>' for o in outlets])
    users_html = "".join([f'<option value="{o}">{o}</option>' for o in Users])

    dispatch_form = f"""
    <form method="post" class="card p-3"
          onsubmit="if (!confirm('Do you want to proceed dispatching ' 
          + document.querySelector('[name=crates_sent]').value 
          + ' crates to outlet ' 
          + document.querySelector('[name=outlet_name]').value 
          + ' by staff ' 
          + document.querySelector('[name=staff_name]').value + '?')) {{
              document.querySelector('[name=cancelled]').value = 'true';
          }}
          return true;">
      <input type="hidden" name="cancelled" value="false">

      <h2>Record Dispatch</h2>
      <div class="mb-3">
        <label class="form-label">Outlet</label>
        <select name="outlet_name" class="form-select" required>
          <option value="" selected>-- Select Outlet --</option>
          {options_html}
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Crates Left here</label>
        <input type="number" name="crates_sent" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Incharge (Staff Name)</label>
        <select name="staff_name" class="form-select" required>
          <option value="" selected>-- Select Staff --</option>
          {users_html}
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Submit Dispatch</button>
    </form>
    {home_button}
    """

    # Step 3: Handle submission
    if request.method == "POST":
        # Cancelled by user
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        print("DEBUG: branchname =", branchname)
        # Assuming you have an Outlet model with id and name
        outlet_t = Outlet.query.filter_by(name=branchname).first()
        print("DEBUG: outlet_t =", outlet_t)
        warehouse_id = outlet_t.outlet_id if outlet_t else None
        #warehouse_id = request.form.get("outlet_name")
        good_crates = request.form.get("crates_sent")
        worn_crates=0
        disposed_crates=0
        staff_name = request.form.get("staff_name")
        transaction_type = "dispatch"
        notes = branchname

        # Convert crates_sent safely
        try:
            good_crates = int(good_crates)
        except (TypeError, ValueError):
            good_crates = 0

        # Ensure staff_name is a string
        staff_name = str(staff_name or "")

        # Validation: if crates = 0 or staff is missing, stop
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Record dispatch
        #new_dispatch = Dispatch(outlet_name=branchname,
        #                        crates_sent=crates_sent,
        #                        staff_name=staff_name,dispatch_date=datetime.now(timezone.utc))
        
        new_warehouse_rcrd = WarehouseTransaction(
                                Wrhse_outlet_id=warehouse_id,
                                good_crates=good_crates,
                                worn_crates=worn_crates,
                                disposed_crates=disposed_crates,
                                transaction_type=transaction_type,
                                notes=notes,
                                staff_name=staff_name)
        db.session.add(new_warehouse_rcrd)
        db.session.commit()

        flash(f"Dispatch recorded: {good_crates} crates sent to {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Step 4: Render with your existing layout
    return render_template_string(layout, content=dispatch_form)

@app.route("/collect", methods=["GET", "POST"])
def record_collection():
    # At app startup, or before you insert
    db.create_all()

    # Step 1: Fetch branch names from external DB or helper
    outlets = retrieve_outlets()
    outlets = [name for name, name in outlets]

    Users = retrieve_offline_users()

    # Step 2: Build the form HTML dynamically
    options_html = "".join([f'<option value="{o}">{o}</option>' for o in outlets])
    users_html = "".join([f'<option value="{o}">{o}</option>' for o in Users])

    dispatch_form = f"""
    <form method="post" class="card p-3"
          onsubmit="if (!confirm('Do you want to proceed collecting ' 
          + document.querySelector('[name=crates_collected]').value 
          + ' crates from outlet ' 
          + document.querySelector('[name=outlet_name]').value 
          + ' by staff ' 
          + document.querySelector('[name=staff_name]').value + '?')) {{
              document.querySelector('[name=cancelled]').value = 'true';
          }}
          return true;">
      <input type="hidden" name="cancelled" value="false">

      <h2>Record Collection</h2>
      <div class="mb-3">
        <label class="form-label">Outlet</label>
        <select name="outlet_name" class="form-select" required>
          <option value="" selected>-- Select Outlet --</option>
          {options_html}
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Crates Collected Here</label>
        <input type="number" name="crates_collected" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Collected By(Staff Name)</label>
        <select name="staff_name" class="form-select" required>
          <option value="" selected>-- Select Staff --</option>
          {users_html}
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Submit Dispatch</button>
    </form>
    {home_button}
    """

    # Step 3: Handle submission
    if request.method == "POST":
        # Cancelled by user
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        #branchname = request.form.get("outlet_name")
        #crates_collected = request.form.get("crates_collected")
        #staff_name = request.form.get("staff_name")
        branchname = request.form.get("outlet_name")
        print("DEBUG: branchname =", branchname)
        # Assuming you have an Outlet model with id and name
        outlet_t = Outlet.query.filter_by(name=branchname).first()
        print("DEBUG: outlet_t =", outlet_t)
        warehouse_id = outlet_t.outlet_id if outlet_t else None
        #warehouse_id = request.form.get("outlet_name")
        good_crates = request.form.get("crates_collected")
        worn_crates=0
        disposed_crates=0
        staff_name = request.form.get("staff_name")
        transaction_type = "collection"
        notes = branchname

        # Convert crates_sent safely
        try:
            good_crates = int(good_crates)
        except (TypeError, ValueError):
            good_crates = 0

        # Ensure staff_name is a string
        staff_name = str(staff_name or "")

        # Validation: if crates = 0 or staff is missing, stop
        if good_crates <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Record collection
        #new_collection = Collection(outlet_name=branchname,
        #                        crates_collected=crates_collected,
        #                        staff_name=staff_name,collection_date=datetime.now(timezone.utc))
        #db.session.add(new_collection)
        new_warehouse_rcrd = WarehouseTransaction(
                                Wrhse_outlet_id=warehouse_id,
                                good_crates=good_crates,
                                worn_crates=worn_crates,
                                disposed_crates=disposed_crates,
                                transaction_type=transaction_type,
                                notes=notes,
                                staff_name=staff_name)
        db.session.add(new_warehouse_rcrd)
        db.session.commit()

        flash(f"Collection recorded: {good_crates} crates returned from {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Step 4: Render with your existing layout
    return render_template_string(layout, content=dispatch_form)


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

@app.route("/dashboard")
def dashboard():
    # ✅ Ensure at least one warehouse exists
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
    retrieve_outlets()  
    # Get all outlet names from Dispatch and Collection
    #dispatch_outlets = db.session.query(Dispatch.outlet_name).distinct()
    #collection_outlets = db.session.query(Collection.outlet_name).distinct()

    dispatched_outlets = (
        db.session.query(WarehouseTransaction.Wrhse_outlet_id)
        .distinct()
        .all()
    )

    #dispatched_outlets = db.session.query(WarehouseTransaction.warehouse_id).distinct()
    #collection_outlets = db.session.query(WarehouseTransaction.outlet_name).distinct()
   
    outlet_ids = [id for (id,) in dispatched_outlets]

    #outlets = retrieve_outlets()
    outlet_names = (
    db.session.query(Outlet.name)
    .filter(Outlet.id.in_(outlet_ids))
    .all()
)

    # Flatten the list of tuples
    all_outlets = [name for (name,) in outlet_names]

    #outlets = [name for name, name in dispatched_outlets]
    #all_outlets=outlets
    # Union them together
    #all_outlets = set([o[0] for o in dispatch_outlets] + [o[0] for o in collection_outlets])




    # Build outlet rows
    #rows = ""
    #for outlet_name in all_outlets:
    #    dispatched = db.session.query(db.func.sum(Dispatch.crates_sent))\
    #                           .filter_by(outlet_name=outlet_name).scalar() or 0
    #    collected = db.session.query(db.func.sum(Collection.crates_collected))\
    #                           .filter_by(outlet_name=outlet_name).scalar() or 0
    #    variance = dispatched - collected
    #    color = "table-danger" if variance > 0 else "table-success"
    #    rows += f"<tr><td>{outlet_name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"


    rows = ""
    for outlet_name in all_outlets:
      collected = (
      db.session.query(db.func.sum(WarehouseTransaction.good_crates))
      .filter(
          WarehouseTransaction.notes == outlet_name,
          WarehouseTransaction.transaction_type == 'collection'
      )
      .scalar()
      ) or 0
      
      dispatched = (
      db.session.query(db.func.sum(WarehouseTransaction.good_crates))
      .filter(
          WarehouseTransaction.notes == outlet_name,
          WarehouseTransaction.transaction_type == 'dispatch'
      )
      .scalar()
      ) or 0
      variance = dispatched - collected
      color = "table-danger" if variance > 0 else "table-success"
      rows += f"<tr><td>{outlet_name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    total_collected = (
      db.session.query(db.func.sum(WarehouseTransaction.good_crates))
      .filter(WarehouseTransaction.transaction_type == 'collection')
      .scalar()
      ) or 0

    total_dispatched = (
      db.session.query(db.func.sum(WarehouseTransaction.good_crates))
      .filter(WarehouseTransaction.transaction_type == 'dispatch')
      .scalar()
      ) or 0

    # Warehouse summary calculations
    warehouse = Warehouse.query.first()  # adjust if multiple warehouses
    if warehouse:
        recent_stcktake_crate= recent_wrhse_crates_stocktake_count()
      
        #total_available = (warehouse.good_crates or 0) + (warehouse.worn_crates or 0)
        #total_available =recent_stcktake_crate - total_dispatched + total_collected
        total_available =recent_stcktake_crate - total_dispatched + total_collected

        #total_dispatched = warehouse.dispatched_crates or 0
        #total_collected = warehouse.collected_crates or 0
        variance = total_collected - total_dispatched 
        #variance = total_available - total_dispatched + total_collected
        #denominator = total_available + total_dispatched + total_collected
        #denominator = recent_stcktake_crate + total_dispatched + total_collected
        denominator = recent_stcktake_crate  # baseline stocktake count
        available_pct = (total_available / denominator * 100) if denominator > 0 else 0

        warehouse_row = f"""
        <tr>
          <td>{warehouse.name}</td>
          <td>{recent_stcktake_crate}</td>
          <td>{total_available}</td>
          <td>{total_dispatched}</td>
          <td>{total_collected}</td>
          <td>{variance}</td>
          <td>{available_pct:.2f}%</td>
          <td>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#stocktakeModal">
              Crates Stocktake
            </button>
          </td>
        </tr>
        """
    else:
        warehouse_row = """
        <tr>
          <td colspan="7" style="text-align:center; color:red;">
            No warehouse record found. Please create one.
          </td>
        </tr>
        """
    
    Users = retrieve_offline_users()
    users_html = "".join([f'<option value="{o}">{o}</option>' for o in Users])
    
    most_recent_stocktake = (
        WarehouseTransaction.query
        .filter_by(transaction_type="stocktake", Wrhse_outlet_id=1)
        .order_by(WarehouseTransaction.timestamp.desc())
        .first()
    )
    
    #if most_recent_stocktake:
    #  last_stocktake_time = most_recent_stocktake.timestamp.strftime("%d %B %Y, %H:%M")
    #  warehouse_summary_text = f"Warehouse Summary : last Stocktake done on {last_stocktake_time}"
    #else:
    #  warehouse_summary_text = "Warehouse Summary : No stocktake transactions found"
    if most_recent_stocktake:
        last_stocktake_time = most_recent_stocktake.timestamp.strftime("%d %B %Y, %H:%M")
        warehouse_summary_text = f'Warehouse Summary : last Stocktake done on <span style="color:blue;">{last_stocktake_time}</span>'
    else:
        warehouse_summary_text = '<span style="color:red;">Warehouse Summary : No stocktake transactions found</span>'



    # Merge warehouse summary on top, outlets below, plus modal form
    content = f"""
    <h2>
      <a href="/" class="btn btn-secondary">Back to Home</a>
      &nbsp;Dashboard
    </h2>

    <!--<h3>Warehouse Summary</h3>--> 
    <h2>{ warehouse_summary_text }</h2>

    <table class="table table-bordered">
      <thead>
        <tr>
          <th>Warehouse</th>
          <th>Last Stocktake</th>
          <th>Total Available</th>
          <th>Total Dispatched</th>
          <th>Total Collected</th>
          <th>Total Variance</th>
          <th>Available %</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>{warehouse_row}</tbody>
    </table>

    
    <!-- Stocktake Modal -->
    <div class="modal fade" id="stocktakeModal" tabindex="-1" aria-labelledby="stocktakeModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <form method="POST" action="/warehouse/{warehouse.id if warehouse else 0}/stocktake">
            <div class="modal-header">
              <h5 class="modal-title" id="stocktakeModalLabel">Crates Stocktake - {warehouse.name if warehouse else ''}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <label for="good_crates">Good Crates (usable)</label>
              <input type="number" name="good_crates" min="0" class="form-control" value="{warehouse.good_crates if warehouse else 0}">

              <label for="worn_crates" class="mt-2">Worn-out but usable Crates</label>
              <input type="number" name="worn_crates" min="0" class="form-control" readonly value="{warehouse.worn_crates if warehouse else 0}">

              <label for="disposed_crates" class="mt-2">Crates to Dispose</label>
              <input type="number" name="disposed_crates" min="0" class="form-control" value="{warehouse.disposed_crates if warehouse else 0}">
              
              <label for="stocktake_by" class="mt-2">stocktake by</label>
              <select name="staff_name" class="form-select mt-2" required>
              <option value="" selected>-- Select Staff --</option>
              { users_html }
              </select>

              <label for="description" class="mt-2">Notes / Description</label>
              <textarea name="description" rows="3" class="form-control"></textarea>
            </div>
            <div class="modal-footer">
              <button type="submit" class="btn btn-success">Submit Stocktake</button>
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <h3>Outlet Summary</h3>
    <table class="table table-bordered">
      <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """
    return render_template_string(layout, content=content)

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
    warehouse_id = Whrsh_Outlets_id
    good_crates = int(request.form.get('good_crates', 0))
    worn_crates = int(request.form.get('worn_crates', 0))
    disposed_crates = int(request.form.get('disposed_crates', 0))
    transaction_type ="stocktake"
    #description = request.form.get('description', '')
    #ware_hse_name = warehouse_id
  
    # Query the Warehouse table where Whrsh_Outlets_id matches
    warehouse = Warehouse.query.filter_by(Whrsh_Outlets_id=warehouse_id).first()

    if warehouse:
        warehsename = warehouse.name
        print("DEBUG: warehsename =", warehsename)
    else:
        print("No warehouse found for outlet_id =", warehouse_id)

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
       notes = warehsename,
        staff_name=staff_name
    )

    db.session.add(txn)
    db.session.commit()

    flash("Stocktake updated successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route("/manage_users", methods=["GET", "POST"])
def manage_users():
    #message = ""

    create_message = ""
    update_message = ""
    delete_message = ""

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
          name = request.form.get("name")

          # Check if user already exists
          existing_user = Users.query.filter_by(staff_name=name).first()
          if existing_user:
              create_message = f"User '{name}' already exists!"
          else:
              new_user = Users(staff_name=name)
              db.session.add(new_user)
              db.session.commit()
              create_message = f"User '{name}' added successfully!"

        elif action == "update":
          existing_userid = request.form.get("staff_name")
          print("DEBUG: existing_name =", existing_userid)
          new_name = request.form.get("new_name")
          print("DEBUG: new_name =", new_name)

          if not new_name:
            update_message = "New name is required."
          else:
            user = Users.query.get(existing_userid)
            #user = Users.query.filter_by(username=existing_name).first()
            print("DEBUG: user object =", user)
            if user:
                oldname=user.staff_name
                user.staff_name = new_name   # update the field directly
                db.session.commit()
                update_message = f"User '{oldname}' updated to '{new_name}' successfully!"
            else:
                update_message = "User not found."


        elif action == "delete":
            # Delete staff
            user_id = request.form.get("del_username")
            if not user_id:
              return
            user = Users.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                delete_message = f"User '{user.staff_name}' deleted successfully!"
            else:
                delete_message = "User not found."

    # Build forms dynamically
    #users = Users.query.all()
    #users=retrieve_users()
    #user_options = "".join([f"<option value='{u.id}'>{u.name}</option>" for u in users])
    users = Users.query.all()   # returns list of Users objects
    user_options = "".join([f"<option value='{u.id}'>{u.staff_name}</option>" for u in users])


    manage_users_form = f"""
    <div class="card p-3">

      <!-- Create new staff -->
      <!--div class="border p-3 mb-3 rounded bg-light"-->
      <div class="border p-1 mb-1 rounded bg-opacity-20">
        <h5 class="text-center">➕ Add Staff</h5>
        <form method="post" 
              onsubmit="return confirm('Do you want to proceed creating user ' + document.querySelector('[name=name]').value + '?');">
          <input type="hidden" name="action" value="create">
          <div class="mb-1">
            <label class="form-label">User Name</label>
            <input type="text" name="name" class="form-control" required>
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-primary">Add User</button>
          </div>
          <p class="mt-2 text-success">{create_message}</p>
        </form>
      </div>

      <!-- Update staff -->
      <!--div class="border p-3 mb-3 rounded bg-warning bg-opacity-25"-->
      <div class="border p-1 mb-1 rounded bg-warning bg-opacity-25">
        <h5 class="text-center">✏️ Update Staff</h5>
        <form method="post" 
          onsubmit="return confirm('Do you want to update user ' + document.querySelector('[name=username]').options[document.querySelector('[name=username]').selectedIndex].text + ' to ' + document.querySelector('[name=new_name]').value + '?');">
          <input type="hidden" name="action" value="update">
          <div class="mb-1">
            <label class="form-label">Select User</label>
            <select name="username" class="form-select"> required>
             <option value="" selected>-- Select User --</option>
             <{user_options}>
             </select>
          </div>
          <div class="mb-1">
            <label class="form-label">New Name</label>
            <input type="text" name="new_name" class="form-control" required>
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-warning">Update User</button>
          </div>
          <p class="mt-2 text-success">{update_message}</p>
        </form>
      </div>

      <!-- Delete staff -->
      <!--div class="border p-3 mb-3 rounded bg-danger bg-opacity-25"-->
      <div class="border p-1 mb-1 rounded bg-danger bg-opacity-25">
        <h5 class="text-center">🗑️ Delete Staff</h5>
        <form method="post" 
              onsubmit="return confirm('Are you sure you want to delete user ' + document.querySelector('[name=del_username]').options[document.querySelector('[name=del_username]').selectedIndex].text + '?');">
          <input type="hidden" name="action" value="delete">
          <div class="mb-1">
            <label class="form-label">Select User</label>
            <select name="del_username" class="form-select" required>
            <option value="" selected>-- Select User --</option>
             <{user_options}>
             </select>
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-danger">Delete User</button>
          </div>
          <p class="mt-2 text-success">{delete_message}</p>
        </form>
      </div>

    </div>
    {home_button}
    """
    return render_template_string(layout, content=manage_users_form)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)