from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---
class Outlet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200))

class Dispatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=False)
    crates_sent = db.Column(db.Integer, nullable=False)
    staff_id = db.Column(db.String(50), nullable=False)

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=False)
    crates_collected = db.Column(db.Integer, nullable=False)
    staff_id = db.Column(db.String(50), nullable=False)

# --- Layout Template with Bootstrap ---
layout = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Crate Tracker</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container mt-4">
  <h1 class="mb-4">📦 Crate Tracker Dashboard</h1>
  {{ content|safe }}
</body>
</html>
"""

# --- Forms ---
dispatch_form = """
<form method="post" class="card p-3">
  <h2>Record Dispatch</h2>
  <div class="mb-3">
    <label class="form-label">Outlet ID</label>
    <input type="number" name="outlet_id" class="form-control">
  </div>
  <div class="mb-3">
    <label class="form-label">Crates Sent</label>
    <input type="number" name="crates_sent" class="form-control">
  </div>
  <div class="mb-3">
    <label class="form-label">Staff ID</label>
    <input type="text" name="staff_id" class="form-control">
  </div>
  <button type="submit" class="btn btn-success">Submit</button>
</form>
"""

collection_form = """
<form method="post" class="card p-3">
  <h2>Record Collection</h2>
  <div class="mb-3">
    <label class="form-label">Outlet ID</label>
    <input type="number" name="outlet_id" class="form-control">
  </div>
  <div class="mb-3">
    <label class="form-label">Crates Collected</label>
    <input type="number" name="crates_collected" class="form-control">
  </div>
  <div class="mb-3">
    <label class="form-label">Staff ID</label>
    <input type="text" name="staff_id" class="form-control">
  </div>
  <button type="submit" class="btn btn-warning">Submit</button>
</form>
"""

# --- Routes ---
@app.route("/")
def home():
    # Build a mini summary table of all outlets
    outlets = Outlet.query.all()
    rows = ""
    for o in outlets:
        dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=o.id).scalar() or 0
        collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=o.id).scalar() or 0
        variance = dispatched - collected
        color = "table-danger" if variance > 0 else "table-success"
        rows += f"<tr><td>{o.name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    summary_table = f"""
    <h2>Outlet Summary</h2>
    <table class="table table-bordered">
      <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """

    shortcuts = """
    <div class="d-grid gap-3 mb-4">
      <a href="/dispatch" class="btn btn-success btn-lg">➕ Record Dispatch</a>
      <a href="/collect" class="btn btn-warning btn-lg">📥 Record Collection</a>
      <a href="/reconcile/1" class="btn btn-info btn-lg">📊 Reconcile Outlet 1</a>
      <a href="/dashboard" class="btn btn-primary btn-lg">📋 View All Outlets Dashboard</a>
    </div>
    """

    content = shortcuts + summary_table
    return render_template_string(layout, content=content)

@app.route("/dispatch", methods=["GET", "POST"])
def record_dispatch():
    if request.method == "POST":
        d = Dispatch(
            outlet_id=int(request.form["outlet_id"]),
            crates_sent=int(request.form["crates_sent"]),
            staff_id=request.form["staff_id"]
        )
        db.session.add(d)
        db.session.commit()
        content = "<div class='alert alert-success'>Dispatch recorded successfully!</div>"
        return render_template_string(layout, content=content)
    return render_template_string(layout, content=dispatch_form)

@app.route("/collect", methods=["GET", "POST"])
def record_collection():
    if request.method == "POST":
        c = Collection(
            outlet_id=int(request.form["outlet_id"]),
            crates_collected=int(request.form["crates_collected"]),
            staff_id=request.form["staff_id"]
        )
        db.session.add(c)
        db.session.commit()
        content = "<div class='alert alert-warning'>Collection recorded successfully!</div>"
        return render_template_string(layout, content=content)
    return render_template_string(layout, content=collection_form)

@app.route("/reconcile/<int:outlet_id>")
def reconcile_outlet(outlet_id):
    dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=outlet_id).scalar() or 0
    collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=outlet_id).scalar() or 0
    variance = dispatched - collected
    content = f"""
    <h2>Reconciliation for Outlet {outlet_id}</h2>
    <table class="table table-bordered">
      <tr><th>Dispatched</th><td>{dispatched}</td></tr>
      <tr><th>Collected</th><td>{collected}</td></tr>
      <tr class="table-{ 'danger' if variance>0 else 'success' }">
        <th>Variance</th><td>{variance}</td>
      </tr>
    </table>
    <a href="/" class="btn btn-secondary">Back to Home</a>
    """
    return render_template_string(layout, content=content)

@app.route("/dashboard")
def dashboard():
    outlets = Outlet.query.all()
    rows = ""
    for o in outlets:
        dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=o.id).scalar() or 0
        collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=o.id).scalar() or 0
        variance = dispatched - collected
        color = "table-danger" if variance > 0 else "table-success"
        rows += f"<tr><td>{o.name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    content = f"""
    <h2>Outlet Dashboard</h2>
    <table class="table table-bordered">
      <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <a href="/" class="btn btn-secondary">Back to Home</a>
    """
    return render_template_string(layout, content=content)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
