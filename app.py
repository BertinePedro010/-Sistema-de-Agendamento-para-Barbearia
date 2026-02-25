from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"


def conectar():
    conn = sqlite3.connect("agendamentos.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================
# CRIAÇÃO DAS TABELAS
# =========================
with conectar() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            idade INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            servico_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
            FOREIGN KEY (servico_id) REFERENCES servicos(id) ON DELETE CASCADE
        )
    """)


# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin01" and request.form["password"] == "admin01":
            session["logado"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if not session.get("logado"):
        return redirect("/")

    conn = conectar()

    agendamentos = conn.execute("""
        SELECT 
            a.id,
            c.nome AS cliente,
            c.telefone,
            a.data,
            a.horario,
            s.nome AS servico,
            s.preco
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        JOIN servicos s ON a.servico_id = s.id
        ORDER BY a.data, a.horario
    """).fetchall()

    total_agendamentos = len(agendamentos)
    faturamento = sum([ag["preco"] for ag in agendamentos]) if agendamentos else 0

    dados_grafico = conn.execute("""
        SELECT data, COUNT(*) as total
        FROM agendamentos
        GROUP BY data
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        agendamentos=agendamentos,
        total_agendamentos=total_agendamentos,
        faturamento=faturamento,
        dados_grafico=dados_grafico
    )


# =========================
# CLIENTES
# =========================
@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if not session.get("logado"):
        return redirect("/")

    conn = conectar()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO clientes (nome, telefone, idade) VALUES (?, ?, ?)",
            (request.form["nome"], request.form["telefone"], request.form["idade"])
        )
        conn.commit()

    busca = request.args.get("busca")

    if busca:
        clientes = conn.execute(
            "SELECT * FROM clientes WHERE nome LIKE ?",
            ('%' + busca + '%',)
        ).fetchall()
    else:
        clientes = conn.execute("SELECT * FROM clientes").fetchall()

    conn.close()
    return render_template("clientes.html", clientes=clientes)


# =========================
# SERVIÇOS
# =========================
@app.route("/servicos", methods=["GET", "POST"])
def servicos():
    if not session.get("logado"):
        return redirect("/")

    conn = conectar()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO servicos (nome, preco) VALUES (?, ?)",
            (request.form["nome"], request.form["preco"])
        )
        conn.commit()

    servicos = conn.execute("SELECT * FROM servicos").fetchall()
    conn.close()
    return render_template("servicos.html", servicos=servicos)


# =========================
# NOVO AGENDAMENTO
# =========================
@app.route("/novo", methods=["GET", "POST"])
def novo():
    if not session.get("logado"):
        return redirect("/")

    conn = conectar()

    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    servicos = conn.execute("SELECT * FROM servicos").fetchall()

    if request.method == "POST":
        data = request.form["data"]
        horario = request.form["horario"]

        existente = conn.execute(
            "SELECT * FROM agendamentos WHERE data=? AND horario=?",
            (data, horario)
        ).fetchone()

        if existente:
            conn.close()
            return "Horário já ocupado!"

        conn.execute(
            "INSERT INTO agendamentos (cliente_id, servico_id, data, horario) VALUES (?, ?, ?, ?)",
            (request.form["cliente"], request.form["servico"], data, horario)
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    conn.close()
    return render_template("novo.html", clientes=clientes, servicos=servicos)


# =========================
# EDITAR AGENDAMENTO
# =========================
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if not session.get("logado"):
        return redirect("/")

    conn = conectar()

    if request.method == "POST":
        conn.execute("""
            UPDATE agendamentos
            SET cliente_id=?, servico_id=?, data=?, horario=?
            WHERE id=?
        """, (
            request.form["cliente"],
            request.form["servico"],
            request.form["data"],
            request.form["horario"],
            id
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    agendamento = conn.execute(
        "SELECT * FROM agendamentos WHERE id=?",
        (id,)
    ).fetchone()

    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    servicos = conn.execute("SELECT * FROM servicos").fetchall()

    conn.close()

    return render_template(
        "editar.html",
        agendamento=agendamento,
        clientes=clientes,
        servicos=servicos
    )


# =========================
# EXCLUIR AGENDAMENTO
# =========================
@app.route("/excluir/<int:id>")
def excluir(id):
    if not session.get("logado"):
        return redirect("/")

    conn = conectar()
    conn.execute("DELETE FROM agendamentos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)