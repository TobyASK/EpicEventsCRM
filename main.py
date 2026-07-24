#!/usr/bin/env python3

import sys

from rich.console import Console
from rich.prompt import Prompt

from cli import cli
from config import SessionLocal, init_db
from controllers.auth_controller import AuthController
from models import Employee


console = Console()


def _run_cli(args: list[str]) -> bool:
    """Execute une commande Click en mode programme depuis le menu."""
    try:
        cli.main(args=args, prog_name="main.py", standalone_mode=False)
        return True
    except SystemExit:
        return False
    except KeyboardInterrupt:
        console.print("[yellow]Action annulee.[/yellow]")
        return False
    except Exception as exc:
        console.print(f"[bold red][X] Erreur: {exc}[/bold red]")
        return False


def _get_current_user() -> Employee | None:
    """Retourne l'utilisateur courant si une session valide existe."""
    db = SessionLocal()
    try:
        return AuthController(db).get_current_user()
    finally:
        db.close()


def _ensure_authenticated() -> bool:
    """Garantit qu'un utilisateur est connecté avant une action protégée."""
    if _get_current_user() is not None:
        return True

    console.print("[yellow]Vous devez être connecté pour cette action.[/yellow]")
    if not _run_cli(["login"]):
        return False
    return _get_current_user() is not None


def _ask_int(label: str) -> int | None:
    """Demande un entier et retourne None en cas d'annulation."""
    while True:
        try:
            value = Prompt.ask(label)
            return int(value)
        except KeyboardInterrupt:
            console.print("\n[yellow]Saisie annulee.[/yellow]")
            return None
        except ValueError:
            console.print("[yellow]Entrez un nombre entier valide.[/yellow]")


def _employee_menu() -> None:
    """Sous-menu des actions employes."""
    while True:
        console.print("\n[bold cyan]Employes[/bold cyan]")
        console.print("1. Lister")
        console.print("2. Creer")
        console.print("3. Modifier")
        console.print("4. Supprimer")
        console.print("0. Retour")

        choice = Prompt.ask("Choix", choices=["0", "1", "2", "3", "4"], default="0")
        if choice == "0":
            return
        if choice == "1":
            _run_cli(["employee", "list"])
        elif choice == "2":
            _run_cli(["employee", "create"])
        elif choice == "3":
            _run_cli(["employee", "list"])
            employee_id = _ask_int("ID employe")
            if employee_id is not None:
                _run_cli(["employee", "update", str(employee_id)])
        elif choice == "4":
            _run_cli(["employee", "list"])
            employee_id = _ask_int("ID employe")
            if employee_id is not None:
                _run_cli(["employee", "delete", str(employee_id)])


def _client_menu() -> None:
    """Sous-menu des actions clients."""
    while True:
        console.print("\n[bold cyan]Clients[/bold cyan]")
        console.print("1. Lister tous")
        console.print("2. Lister les miens")
        console.print("3. Creer")
        console.print("4. Modifier")
        console.print("0. Retour")

        choice = Prompt.ask("Choix", choices=["0", "1", "2", "3", "4"], default="0")
        if choice == "0":
            return
        if choice == "1":
            _run_cli(["client", "list"])
        elif choice == "2":
            _run_cli(["client", "list", "--mine"])
        elif choice == "3":
            _run_cli(["client", "create"])
        elif choice == "4":
            _run_cli(["client", "list"])
            client_id = _ask_int("ID client")
            if client_id is not None:
                _run_cli(["client", "update", str(client_id)])


def _contract_menu() -> None:
    """Sous-menu des actions contrats."""
    while True:
        console.print("\n[bold cyan]Contrats[/bold cyan]")
        console.print("1. Lister tous")
        console.print("2. Lister non signes")
        console.print("3. Lister non payes")
        console.print("4. Creer")
        console.print("5. Modifier")
        console.print("6. Signer")
        console.print("0. Retour")

        choice = Prompt.ask("Choix", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")
        if choice == "0":
            return
        if choice == "1":
            _run_cli(["contract", "list"])
        elif choice == "2":
            _run_cli(["contract", "list", "--unsigned"])
        elif choice == "3":
            _run_cli(["contract", "list", "--unpaid"])
        elif choice == "4":
            _run_cli(["contract", "create"])
        elif choice == "5":
            _run_cli(["contract", "list"])
            contract_id = _ask_int("ID contrat")
            if contract_id is not None:
                _run_cli(["contract", "update", str(contract_id)])
        elif choice == "6":
            _run_cli(["contract", "list", "--unsigned"])
            contract_id = _ask_int("ID contrat")
            if contract_id is not None:
                _run_cli(["contract", "sign", str(contract_id)])


def _event_menu() -> None:
    """Sous-menu des actions evenements."""
    while True:
        console.print("\n[bold cyan]Evenements[/bold cyan]")
        console.print("1. Lister tous")
        console.print("2. Lister les miens")
        console.print("3. Lister sans support")
        console.print("4. Creer")
        console.print("5. Modifier")
        console.print("6. Assigner un support")
        console.print("0. Retour")

        choice = Prompt.ask("Choix", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")
        if choice == "0":
            return
        if choice == "1":
            _run_cli(["event", "list"])
        elif choice == "2":
            _run_cli(["event", "list", "--mine"])
        elif choice == "3":
            _run_cli(["event", "list", "--no-support"])
        elif choice == "4":
            _run_cli(["event", "create"])
        elif choice == "5":
            _run_cli(["event", "list"])
            event_id = _ask_int("ID evenement")
            if event_id is not None:
                _run_cli(["event", "update", str(event_id)])
        elif choice == "6":
            _run_cli(["event", "list", "--no-support"])
            event_id = _ask_int("ID evenement")
            if event_id is None:
                continue
            _run_cli(["employee", "list"])
            support_id = _ask_int("ID support")
            if support_id is not None:
                _run_cli(["event", "assign-support", str(event_id), str(support_id)])


def _interactive_menu() -> None:
    """Affiche un menu interactif simple pour les actions principales."""
    while True:
        user = _get_current_user()
        if user:
            status = f"Connecté: {user.email} ({user.department.value})"
        else:
            status = "Non connecté"

        console.print("\n[bold cyan]Epic Events CRM - Menu interactif[/bold cyan]")
        console.print(f"[dim]{status}[/dim]")
        console.print("1. Login")
        console.print("2. Logout")
        console.print("3. Actions employes")
        console.print("4. Actions clients")
        console.print("5. Actions contrats")
        console.print("6. Actions evenements")
        console.print("7. Test erreur Sentry")
        console.print("0. Quitter")

        try:
            choice = Prompt.ask("Choix", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="0")
        except KeyboardInterrupt:
            console.print("\n[green]Au revoir.[/green]")
            return

        if choice == "0":
            console.print("[green]Au revoir.[/green]")
            return
        if choice == "1":
            _run_cli(["login"])
        elif choice == "2":
            if _get_current_user() is None:
                console.print("[yellow]Aucune session active.[/yellow]")
                continue
            _run_cli(["logout"])
        elif choice == "3":
            if _ensure_authenticated():
                _employee_menu()
        elif choice == "4":
            if _ensure_authenticated():
                _client_menu()
        elif choice == "5":
            if _ensure_authenticated():
                _contract_menu()
        elif choice == "6":
            if _ensure_authenticated():
                _event_menu()
        elif choice == "7":
            _run_cli(["sentry-raise"])


if __name__ == "__main__":
    try:
        # Initialisation idempotente: sûre à chaque lancement.
        init_db()
    except Exception as exc:
        console.print(f"[bold red][X] Erreur initialisation DB: {exc}[/bold red]")
        raise SystemExit(1)

    if len(sys.argv) > 1:
        cli()
    else:
        _interactive_menu()
