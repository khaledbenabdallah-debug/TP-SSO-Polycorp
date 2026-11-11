import os
from flask import Flask, request, redirect, session
from onelogin.saml2.auth import OneLogin_Saml2_Auth

BASE = os.path.dirname(os.path.abspath(__file__))
IDP_CERT = open(os.path.join(BASE, "idp_cert.txt")).read().strip()

SAML_SETTINGS = {
    "strict": True,
    "debug": True,
    "sp": {
        "entityId": "portail-rh",
        "assertionConsumerService": {
            "url": "http://localhost:5002/saml/acs",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
    },
    "idp": {
        "entityId": "http://localhost:8080/realms/polycorp",
        "singleSignOnService": {
            "url": "http://localhost:8080/realms/polycorp/protocol/saml",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "x509cert": IDP_CERT,
    },
    "security": {
        "wantMessagesSigned": True,
    },
}

app = Flask(__name__)
app.secret_key = "cle-session-rh-lab"
app.config["SESSION_COOKIE_NAME"] = "session_rh"


def saml_auth():
    req = {
        "https": "off",
        "http_host": "localhost:5002",
        "server_port": "5002",
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
    }
    return OneLogin_Saml2_Auth(req, old_settings=SAML_SETTINGS)


@app.route("/")
def accueil():
    u = session.get("user")
    if not u:
        return '<h1>Portail RH</h1><a href="/login">Se connecter avec Keycloak (SAML)</a>'
    return (
        "<h1>Portail RH</h1>"
        f"<p>Connecté : <b>{u['nameid']}</b></p>"
        f"<p>Nom : {u['nom']}</p>"
        f"<p>Email : {u['email']}</p>"
        f"<p>Rôles : {', '.join(u['roles'])}</p>"
        f"<p>Attributs SAML reçus : {u['attrs']}</p>"
        '<p><a href="/rh">Espace RH</a></p>'
        '<a href="/logout">Se déconnecter</a>'
    )


@app.route("/login")
def login():
    auth = saml_auth()
    return redirect(auth.login())


@app.route("/saml/acs", methods=["POST"])
def acs():
    auth = saml_auth()
    auth.process_response()
    errors = auth.get_errors()
    if errors or not auth.is_authenticated():
        return (
            f"<h1>Erreur SAML</h1><p>{errors}</p>"
            f"<p>{auth.get_last_error_reason()}</p>",
            400,
        )
    attrs = auth.get_attributes()
    with open(os.path.join(BASE, "last_assertion.xml"), "w") as f:
        f.write(auth.get_last_response_xml())
    session["user"] = {
        "nameid": auth.get_nameid(),
        "nom": " ".join(attrs.get("givenName", []) + attrs.get("surname", [])),
        "email": ", ".join(attrs.get("email", [])),
        "roles": attrs.get("Role", []),
        "attrs": attrs,
    }
    return redirect("/")


@app.route("/rh")
def espace_rh():
    u = session.get("user")
    if not u:
        return redirect("/login")
    if "acces-rh" not in u["roles"]:
        return (
            "<h1>Accès refusé</h1>"
            f"<p>{u['nameid']} est authentifié mais n'a pas le rôle acces-rh.</p>"
            '<a href="/">Retour</a>',
            403,
        )
    return (
        "<h1>Espace RH</h1>"
        f"<p>Bienvenue {u['nom']}, accès autorisé (rôle acces-rh).</p>"
        '<a href="/">Retour</a>'
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(port=5002)
