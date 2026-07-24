
from datetime import datetime

import click
import sentry_sdk
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from config import SessionLocal
from controllers.auth_controller import AuthController
from controllers.client_controller import ClientController
from controllers.contract_controller import ContractController
from controllers.employee_controller import EmployeeController
from controllers.event_controller import EventController
from utils import init_sentry


console = Console()


def run_with_db(action, require_auth=False):
    """Exécute une action dans une session DB avec gestion d'erreurs."""
    db = SessionLocal()
    try:
        if require_auth:
            current_user = AuthController(db).require_auth()
            return action(db, current_user)
        return action(db)
    except Exception as exc:
        console.print(f"[bold red][X] Erreur: {exc}[/bold red]")
        return None
    finally:
        db.close()


@click.group(no_args_is_help=True)
def cli():
    """Point d'entrée des commandes CLI."""
    init_sentry()


@cli.command()
@click.option("--email", prompt=True, help="Email de l'employé")
@click.option("--password", prompt=True, hide_input=True, help="Mot de passe")
def login(email, password):
    """Authentifie un utilisateur."""

    def action(db):
        result = AuthController(db).login(email, password)
        console.print("[bold green][OK] Connexion réussie![/bold green]")
        console.print(f"Bienvenue {result['full_name']} ({result['department']})")

    run_with_db(action)


@cli.command()
def logout():
    """Termine la session utilisateur courante."""

    def action(db):
        AuthController(db).logout()
        console.print("[bold green][OK] Déconnexion réussie![/bold green]")

    run_with_db(action)


@cli.command("sentry-raise")
def sentry_raise():
    """Déclenche une exception volontaire pour vérifier Sentry."""
    try:
        raise RuntimeError("Erreur de test Sentry volontaire")
    except RuntimeError as exc:
        sentry_sdk.capture_exception(exc)
        raise


@cli.group()
def employee():
    """Commandes liées aux employés."""
    pass


@employee.command("create")
def employee_create():
    """Crée un employé via prompts interactifs."""

    def action(db, current_user):
        employee_number = Prompt.ask("Numéro d'employé")
        full_name = Prompt.ask("Nom complet")
        email = Prompt.ask("Email")
        password = Prompt.ask("Mot de passe", password=True)
        department = Prompt.ask("Département", choices=["commercial", "support", "gestion"])

        emp = EmployeeController(db).create_employee(
            current_user,
            employee_number,
            full_name,
            email,
            password,
            department,
        )
        console.print(f"[bold green][OK] Employé {emp.full_name} créé avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@employee.command("list")
def employee_list():
    """Affiche la liste des employés."""

    def action(db, current_user):
        employees = EmployeeController(db).get_all_employees(current_user)

        table = Table(title="Liste des Employés")
        table.add_column("ID", style="cyan")
        table.add_column("Numéro", style="magenta")
        table.add_column("Nom", style="green")
        table.add_column("Email", style="yellow")
        table.add_column("Département", style="blue")

        for emp in employees:
            table.add_row(str(emp.id), emp.employee_number, emp.full_name, emp.email, emp.department.value)

        console.print(table)

    run_with_db(action, require_auth=True)


@employee.command("update")
@click.argument("employee_id", type=int)
def employee_update(employee_id):
    """Met à jour un employé."""

    def action(db, current_user):
        controller = EmployeeController(db)
        emp = controller.get_employee_by_id(current_user, employee_id)
        if not emp:
            console.print(f"[bold red][X] Employé {employee_id} non trouvé[/bold red]")
            return

        console.print(f"Modification de: {emp.full_name}")

        full_name = Prompt.ask("Nouveau nom", default=emp.full_name)
        email = Prompt.ask("Nouvel email", default=emp.email)
        department = Prompt.ask(
            "Nouveau département",
            choices=["commercial", "support", "gestion", ""],
            default=emp.department.value,
        )

        updates = {}
        if full_name != emp.full_name:
            updates["full_name"] = full_name
        if email != emp.email:
            updates["email"] = email
        if department and department != emp.department.value:
            updates["department"] = department

        if not updates:
            console.print("[yellow]Aucune modification effectuée[/yellow]")
            return

        controller.update_employee(current_user, employee_id, **updates)
        console.print("[bold green][OK] Employé mis à jour avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@employee.command("delete")
@click.argument("employee_id", type=int)
def employee_delete(employee_id):
    """Supprime un employé."""

    def action(db, current_user):
        controller = EmployeeController(db)
        emp = controller.get_employee_by_id(current_user, employee_id)
        if not emp:
            console.print(f"[bold red][X] Employé {employee_id} non trouvé[/bold red]")
            return

        console.print(f"[yellow]Vous allez supprimer : {emp.full_name} ({emp.email})[/yellow]")
        if not click.confirm("Confirmer la suppression ?"):
            console.print("[yellow]Suppression annulée[/yellow]")
            return

        controller.delete_employee(current_user, employee_id)
        console.print("[bold green][OK] Employé supprimé avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@cli.group()
def client():
    """Commandes liées aux clients."""
    pass


@client.command("create")
def client_create():
    """Crée un client via prompts interactifs."""

    def action(db, current_user):
        full_name = Prompt.ask("Nom complet")
        email = Prompt.ask("Email")
        phone = Prompt.ask("Téléphone")
        company_name = Prompt.ask("Nom de l'entreprise")

        new_client = ClientController(db).create_client(
            current_user,
            full_name,
            email,
            phone,
            company_name,
        )
        console.print(f"[bold green][OK] Client {new_client.full_name} créé avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@client.command("list")
@click.option("--mine", is_flag=True, help="Afficher uniquement mes clients")
def client_list(mine):
    """Affiche les clients, globaux ou personnels."""

    def action(db, current_user):
        controller = ClientController(db)
        if mine:
            clients = controller.get_my_clients(current_user)
            title = "Mes Clients"
        else:
            clients = controller.get_all_clients(current_user)
            title = "Liste des Clients"

        table = Table(title=title)
        table.add_column("ID", style="cyan")
        table.add_column("Nom", style="green")
        table.add_column("Email", style="yellow")
        table.add_column("Téléphone", style="blue")
        table.add_column("Entreprise", style="magenta")
        table.add_column("Contact Commercial", style="red")

        for cli_item in clients:
            table.add_row(
                str(cli_item.id),
                cli_item.full_name,
                cli_item.email,
                cli_item.phone,
                cli_item.company_name,
                cli_item.commercial_contact.full_name,
            )

        console.print(table)

    run_with_db(action, require_auth=True)


@client.command("update")
@click.argument("client_id", type=int)
def client_update(client_id):
    """Met à jour un client."""

    def action(db, current_user):
        controller = ClientController(db)
        cli_item = controller.get_client_by_id(current_user, client_id)
        if not cli_item:
            console.print(f"[bold red][X] Client {client_id} non trouvé[/bold red]")
            return

        console.print(f"Modification de: {cli_item.full_name}")
        full_name = Prompt.ask("Nouveau nom", default=cli_item.full_name)
        email = Prompt.ask("Nouvel email", default=cli_item.email)
        phone = Prompt.ask("Nouveau téléphone", default=cli_item.phone)
        company_name = Prompt.ask("Nouvelle entreprise", default=cli_item.company_name)

        updates = {}
        if full_name != cli_item.full_name:
            updates["full_name"] = full_name
        if email != cli_item.email:
            updates["email"] = email
        if phone != cli_item.phone:
            updates["phone"] = phone
        if company_name != cli_item.company_name:
            updates["company_name"] = company_name

        if not updates:
            console.print("[yellow]Aucune modification effectuée[/yellow]")
            return

        controller.update_client(current_user, client_id, **updates)
        console.print("[bold green][OK] Client mis à jour avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@cli.group()
def contract():
    """Commandes liées aux contrats."""
    pass


@contract.command("create")
def contract_create():
    """Crée un contrat via prompts interactifs."""

    def action(db, current_user):
        client_controller = ClientController(db)
        clients = client_controller.get_all_clients(current_user)
        if not clients:
            console.print("[yellow]Aucun client disponible. Créez un client d'abord.[/yellow]")
            return

        clients_table = Table(title="Clients disponibles")
        clients_table.add_column("ID", style="cyan")
        clients_table.add_column("Nom", style="green")
        clients_table.add_column("Entreprise", style="magenta")
        clients_table.add_column("Commercial", style="yellow")
        for client in clients:
            clients_table.add_row(
                str(client.id),
                client.full_name,
                client.company_name,
                client.commercial_contact.full_name,
            )
        console.print(clients_table)

        contract_number = Prompt.ask("Numéro de contrat")
        client_choices = [str(client.id) for client in clients]
        client_id = int(Prompt.ask("ID du client", choices=client_choices))

        selected_client = next((client for client in clients if client.id == client_id), None)
        if not selected_client:
            raise ValueError(f"Client {client_id} non trouvé")

        default_commercial_id = selected_client.commercial_contact_id

        employee_controller = EmployeeController(db)
        commercials = employee_controller.get_employees_by_department(current_user, "commercial")
        commercials_table = Table(title="Commerciaux disponibles")
        commercials_table.add_column("ID", style="cyan")
        commercials_table.add_column("Nom", style="green")
        commercials_table.add_column("Email", style="yellow")
        for employee in commercials:
            commercials_table.add_row(str(employee.id), employee.full_name, employee.email)
        console.print(commercials_table)

        if not commercials:
            raise ValueError("Aucun commercial disponible")

        commercial_choices = [str(employee.id) for employee in commercials]
        default_commercial_id_str = str(default_commercial_id)
        if default_commercial_id_str not in commercial_choices:
            default_commercial_id_str = commercial_choices[0]

        commercial_contact_id = int(
            Prompt.ask(
                "ID du contact commercial",
                choices=commercial_choices,
                default=default_commercial_id_str,
            )
        )

        total_amount = float(Prompt.ask("Montant total"))
        amount_remaining = Prompt.ask("Montant restant (laisser vide = montant total)", default="")

        cont = ContractController(db).create_contract(
            current_user,
            contract_number,
            client_id,
            total_amount,
            float(amount_remaining) if amount_remaining else None,
            commercial_contact_id,
        )
        console.print(f"[bold green][OK] Contrat {cont.contract_number} créé avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@contract.command("list")
@click.option("--unsigned", is_flag=True, help="Afficher uniquement les contrats non signés")
@click.option("--unpaid", is_flag=True, help="Afficher uniquement les contrats non payés")
def contract_list(unsigned, unpaid):
    """Affiche les contrats selon les filtres demandés."""

    def action(db, current_user):
        controller = ContractController(db)
        if unsigned:
            contracts = controller.get_unsigned_contracts(current_user)
            title = "Contrats Non Signés"
        elif unpaid:
            contracts = controller.get_unpaid_contracts(current_user)
            title = "Contrats Non Payés"
        else:
            contracts = controller.get_all_contracts(current_user)
            title = "Liste des Contrats"

        table = Table(title=title)
        table.add_column("ID", style="cyan")
        table.add_column("Numéro", style="magenta")
        table.add_column("Client", style="green")
        table.add_column("Montant Total", style="yellow")
        table.add_column("Restant", style="blue")
        table.add_column("Signé", style="red")
        table.add_column("Commercial", style="white")

        for cont in contracts:
            table.add_row(
                str(cont.id),
                cont.contract_number,
                cont.client.full_name,
                f"{cont.total_amount}€",
                f"{cont.amount_remaining}€",
                "Oui" if cont.is_signed else "Non",
                cont.commercial_contact.full_name,
            )

        console.print(table)

    run_with_db(action, require_auth=True)


@contract.command("update")
@click.argument("contract_id", type=int)
def contract_update(contract_id):
    """Met à jour un contrat."""

    def action(db, current_user):
        controller = ContractController(db)
        cont = controller.get_contract_by_id(current_user, contract_id)
        if not cont:
            console.print(f"[bold red][X] Contrat {contract_id} non trouvé[/bold red]")
            return

        console.print(f"Modification du contrat: {cont.contract_number}")
        total_amount = Prompt.ask("Nouveau montant total", default=str(cont.total_amount))
        amount_remaining = Prompt.ask("Nouveau montant restant", default=str(cont.amount_remaining))

        updates = {}
        if float(total_amount) != cont.total_amount:
            updates["total_amount"] = float(total_amount)
        if float(amount_remaining) != cont.amount_remaining:
            updates["amount_remaining"] = float(amount_remaining)

        if not updates:
            console.print("[yellow]Aucune modification effectuée[/yellow]")
            return

        controller.update_contract(current_user, contract_id, **updates)
        console.print("[bold green][OK] Contrat mis à jour avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@contract.command("sign")
@click.argument("contract_id", type=int)
def contract_sign(contract_id):
    """Signe un contrat."""

    def action(db, current_user):
        cont = ContractController(db).sign_contract(current_user, contract_id)
        console.print(f"[bold green][OK] Contrat {cont.contract_number} signé avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@cli.group()
def event():
    """Commandes liées aux événements."""
    pass


@event.command("create")
def event_create():
    """Crée un événement via prompts interactifs."""

    def action(db, current_user):
        contract_id = int(Prompt.ask("ID du contrat"))
        event_name = Prompt.ask("Nom de l'événement")
        location = Prompt.ask("Lieu")
        attendees = int(Prompt.ask("Nombre de participants"))

        start_date_str = Prompt.ask("Date de début (YYYY-MM-DD HH:MM)")
        end_date_str = Prompt.ask("Date de fin (YYYY-MM-DD HH:MM)")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")
        notes = Prompt.ask("Notes (optionnel)", default="")

        evt = EventController(db).create_event(
            current_user,
            contract_id,
            event_name,
            start_date,
            end_date,
            location,
            attendees,
            notes if notes else None,
        )
        console.print(f"[bold green][OK] Événement {evt.event_name} créé avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@event.command("list")
@click.option("--mine", is_flag=True, help="Afficher uniquement mes événements")
@click.option("--no-support", is_flag=True, help="Afficher uniquement les événements sans support")
def event_list(mine, no_support):
    """Affiche les événements selon les filtres demandés."""

    def action(db, current_user):
        controller = EventController(db)
        if mine:
            events = controller.get_my_events(current_user)
            title = "Mes Événements"
        elif no_support:
            events = controller.get_events_without_support(current_user)
            title = "Événements Sans Support"
        else:
            events = controller.get_all_events(current_user)
            title = "Liste des Événements"

        table = Table(title=title)
        table.add_column("ID", style="cyan")
        table.add_column("Nom", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("Lieu", style="blue")
        table.add_column("Participants", style="magenta")
        table.add_column("Support", style="red")

        for evt in events:
            support_name = evt.support_contact.full_name if evt.support_contact else "Non assigné"
            table.add_row(
                str(evt.id),
                evt.event_name,
                evt.event_date_start.strftime("%Y-%m-%d %H:%M"),
                evt.location,
                str(evt.attendees),
                support_name,
            )

        console.print(table)

    run_with_db(action, require_auth=True)


@event.command("update")
@click.argument("event_id", type=int)
def event_update(event_id):
    """Met à jour un événement."""

    def action(db, current_user):
        controller = EventController(db)
        evt = controller.get_event_by_id(current_user, event_id)
        if not evt:
            console.print(f"[bold red][X] Événement {event_id} non trouvé[/bold red]")
            return

        console.print(f"Modification de: {evt.event_name}")
        event_name = Prompt.ask("Nouveau nom", default=evt.event_name)
        location = Prompt.ask("Nouveau lieu", default=evt.location)
        attendees = Prompt.ask("Nouveau nombre de participants", default=str(evt.attendees))
        notes = Prompt.ask("Nouvelles notes", default=evt.notes or "")

        updates = {}
        if event_name != evt.event_name:
            updates["event_name"] = event_name
        if location != evt.location:
            updates["location"] = location
        if int(attendees) != evt.attendees:
            updates["attendees"] = int(attendees)
        if notes != (evt.notes or ""):
            updates["notes"] = notes

        if not updates:
            console.print("[yellow]Aucune modification effectuée[/yellow]")
            return

        controller.update_event(current_user, event_id, **updates)
        console.print("[bold green][OK] Événement mis à jour avec succès![/bold green]")

    run_with_db(action, require_auth=True)


@event.command("assign-support")
@click.argument("event_id", type=int)
@click.argument("support_id", type=int)
def event_assign_support(event_id, support_id):
    """Assigne un support à un événement."""

    def action(db, current_user):
        evt = EventController(db).assign_support(current_user, event_id, support_id)
        console.print(f"[bold green][OK] Support assigné à l'événement {evt.event_name}![/bold green]")

    run_with_db(action, require_auth=True)

