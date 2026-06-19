"""
Interface CLI principale de l'application Epic Events CRM
"""
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from config.database import SessionLocal, init_db
from controllers.auth_controller import AuthController
from controllers.employee_controller import EmployeeController
from controllers.client_controller import ClientController
from controllers.contract_controller import ContractController
from controllers.event_controller import EventController
from utils.sentry_logger import init_sentry
from datetime import datetime

console = Console()


@click.group()
def cli():
    """Epic Events CRM - Gestion des clients, contrats et événements"""
    # Initialiser Sentry
    init_sentry()


@cli.command()
def init():
    """Initialise la base de données"""
    try:
        console.print(
            "[bold blue]Initialisation de la base de données..."
            "[/bold blue]")
        init_db()
        console.print(
            "[bold green][OK]Base de données initialisée avec succès!"
            "[/bold green]")
    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")


@cli.command()
@click.option('--email', prompt=True, help="Email de l'employé")
@click.option('--password', prompt=True, hide_input=True,
              help="Mot de passe")
def login(email, password):
    """Se connecter à l'application"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        # Vérifie les identifiants et génère un token JWT stocké
        # dans .auth_token
        result = auth_controller.login(email, password)

        console.print("[bold green][OK]Connexion réussie![/bold green]")
        console.print(
            f"Bienvenue {result['full_name']} "
            f"({result['department']})")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@cli.command()
def logout():
    """Se déconnecter de l'application"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        auth_controller.logout()
        console.print("[bold green][OK]Déconnexion réussie![/bold green]")
    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


# ===== COMMANDES EMPLOYEES =====

@cli.group()
def employee():
    """Gestion des employés"""
    pass


@employee.command('create')
def employee_create():
    """Créer un nouvel employé"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        # Collecter les informations du nouvel employé via des prompts
        employee_number = Prompt.ask("Numéro d'employé")
        full_name = Prompt.ask("Nom complet")
        email = Prompt.ask("Email")
        password = Prompt.ask("Mot de passe", password=True)
        department = Prompt.ask(
            "Département",
            choices=["commercial", "support", "gestion"])

        employee_controller = EmployeeController(db)
        emp = employee_controller.create_employee(
            current_user, employee_number, full_name, email,
            password, department)

        console.print(
            f"[bold green][OK]Employé {emp.full_name} créé "
            f"avec succès![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@employee.command('list')
def employee_list():
    """Lister tous les employés"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        employee_controller = EmployeeController(db)
        employees = employee_controller.get_all_employees(current_user)

        # Construire un tableau Rich avec une colonne par champ
        table = Table(title="Liste des Employés")
        table.add_column("ID", style="cyan")
        table.add_column("Numéro", style="magenta")
        table.add_column("Nom", style="green")
        table.add_column("Email", style="yellow")
        table.add_column("Département", style="blue")

        for emp in employees:
            table.add_row(
                str(emp.id),
                emp.employee_number,
                emp.full_name,
                emp.email,
                emp.department.value
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@employee.command('update')
@click.argument('employee_id', type=int)
def employee_update(employee_id):
    """Mettre à jour un employé"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        employee_controller = EmployeeController(db)
        emp = employee_controller.get_employee_by_id(
            current_user, employee_id)

        if not emp:
            console.print(
                f"[bold red][X]Employé {employee_id} non trouvé"
                f"[/bold red]")
            return

        console.print(f"Modification de: {emp.full_name}")

        # Pré-remplir avec les valeurs actuelles ;
        # entrée vide = pas de changement
        full_name = Prompt.ask(
            "Nouveau nom (laisser vide pour ne pas changer)",
            default=emp.full_name)
        email = Prompt.ask(
            "Nouvel email (laisser vide pour ne pas changer)",
            default=emp.email)
        department = Prompt.ask(
            "Nouveau département (laisser vide pour ne pas changer)",
            choices=["commercial", "support", "gestion", ""],
            default=emp.department.value
        )

        # Construire le dictionnaire des champs modifiés uniquement
        updates = {}
        if full_name != emp.full_name:
            updates['full_name'] = full_name
        if email != emp.email:
            updates['email'] = email
        if department and department != emp.department.value:
            updates['department'] = department

        if updates:
            employee_controller.update_employee(
                current_user, employee_id, **updates)
            console.print(
                "[bold green][OK]Employé mis à jour avec succès!"
                "[/bold green]")
        else:
            console.print(
                "[yellow]Aucune modification effectuée[/yellow]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@employee.command('delete')
@click.argument('employee_id', type=int)
def employee_delete(employee_id):
    """Supprimer un employé"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        employee_controller = EmployeeController(db)
        emp = employee_controller.get_employee_by_id(
            current_user, employee_id)

        if not emp:
            console.print(
                f"[bold red][X]Employé {employee_id} non trouvé"
                f"[/bold red]")
            return

        # Afficher un résumé avant la confirmation pour éviter
        # les suppressions accidentelles
        console.print(
            f"[yellow]Vous allez supprimer : {emp.full_name} "
            f"({emp.email})[/yellow]")
        if not click.confirm("Confirmer la suppression ?"):
            console.print("[yellow]Suppression annulée[/yellow]")
            return

        employee_controller.delete_employee(current_user, employee_id)
        console.print(
            "[bold green][OK]Employé supprimé avec succès![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


# ===== COMMANDES CLIENTS =====

@cli.group()
def client():
    """Gestion des clients"""
    pass


@client.command('create')
def client_create():
    """Créer un nouveau client"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        # Le commercial est automatiquement assigné comme contact
        # commercial du client
        full_name = Prompt.ask("Nom complet")
        email = Prompt.ask("Email")
        phone = Prompt.ask("Téléphone")
        company_name = Prompt.ask("Nom de l'entreprise")

        client_controller = ClientController(db)
        new_client = client_controller.create_client(
            current_user, full_name, email, phone, company_name
        )

        console.print(
            f"[bold green][OK]Client {new_client.full_name} créé "
            f"avec succès![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@client.command('list')
@click.option('--mine', is_flag=True,
              help="Afficher uniquement mes clients")
def client_list(mine):
    """Lister les clients"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        client_controller = ClientController(db)

        # --mine restreint la liste aux clients du commercial connecté
        if mine:
            clients = client_controller.get_my_clients(current_user)
            title = "Mes Clients"
        else:
            clients = client_controller.get_all_clients(current_user)
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
                cli_item.commercial_contact.full_name
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@client.command('update')
@click.argument('client_id', type=int)
def client_update(client_id):
    """Mettre à jour un client"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        client_controller = ClientController(db)
        cli_item = client_controller.get_client_by_id(
            current_user, client_id)

        if not cli_item:
            console.print(
                f"[bold red][X]Client {client_id} non trouvé[/bold red]")
            return

        console.print(f"Modification de: {cli_item.full_name}")

        # Pré-remplir avec les valeurs actuelles
        full_name = Prompt.ask("Nouveau nom", default=cli_item.full_name)
        email = Prompt.ask("Nouvel email", default=cli_item.email)
        phone = Prompt.ask("Nouveau téléphone", default=cli_item.phone)
        company_name = Prompt.ask(
            "Nouvelle entreprise", default=cli_item.company_name)

        # N'envoyer au controller que les champs réellement modifiés
        updates = {}
        if full_name != cli_item.full_name:
            updates['full_name'] = full_name
        if email != cli_item.email:
            updates['email'] = email
        if phone != cli_item.phone:
            updates['phone'] = phone
        if company_name != cli_item.company_name:
            updates['company_name'] = company_name

        if updates:
            client_controller.update_client(
                current_user, client_id, **updates)
            console.print(
                "[bold green][OK]Client mis à jour avec succès!"
                "[/bold green]")
        else:
            console.print(
                "[yellow]Aucune modification effectuée[/yellow]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


# ===== COMMANDES CONTRATS =====

@cli.group()
def contract():
    """Gestion des contrats"""
    pass


@contract.command('create')
def contract_create():
    """Créer un nouveau contrat"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        contract_number = Prompt.ask("Numéro de contrat")
        client_id = int(Prompt.ask("ID du client"))
        total_amount = float(Prompt.ask("Montant total"))
        # Montant restant optionnel : vide = montant total
        amount_remaining = Prompt.ask(
            "Montant restant (laisser vide = montant total)",
            default="")

        contract_controller = ContractController(db)
        cont = contract_controller.create_contract(
            current_user,
            contract_number,
            client_id,
            total_amount,
            float(amount_remaining) if amount_remaining else None
        )

        console.print(
            f"[bold green][OK]Contrat {cont.contract_number} créé "
            f"avec succès![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@contract.command('list')
@click.option('--unsigned', is_flag=True,
              help="Afficher uniquement les contrats non signés")
@click.option('--unpaid', is_flag=True,
              help="Afficher uniquement les contrats non payés")
def contract_list(unsigned, unpaid):
    """Lister les contrats"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        contract_controller = ContractController(db)

        # Les filtres --unsigned et --unpaid permettent à la Gestion
        # d'identifier rapidement les contrats nécessitant une action
        if unsigned:
            contracts = contract_controller.get_unsigned_contracts(
                current_user)
            title = "Contrats Non Signés"
        elif unpaid:
            contracts = contract_controller.get_unpaid_contracts(
                current_user)
            title = "Contrats Non Payés"
        else:
            contracts = contract_controller.get_all_contracts(
                current_user)
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
                cont.commercial_contact.full_name
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@contract.command('update')
@click.argument('contract_id', type=int)
def contract_update(contract_id):
    """Mettre à jour un contrat"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        contract_controller = ContractController(db)
        cont = contract_controller.get_contract_by_id(
            current_user, contract_id)

        if not cont:
            console.print(
                f"[bold red][X]Contrat {contract_id} non trouvé"
                f"[/bold red]")
            return

        console.print(
            f"Modification du contrat: {cont.contract_number}")

        # Pré-remplir avec les montants actuels pour faciliter la saisie
        total_amount = Prompt.ask(
            "Nouveau montant total", default=str(cont.total_amount))
        amount_remaining = Prompt.ask(
            "Nouveau montant restant",
            default=str(cont.amount_remaining))

        # N'envoyer que les champs dont la valeur a changé
        updates = {}
        if float(total_amount) != cont.total_amount:
            updates['total_amount'] = float(total_amount)
        if float(amount_remaining) != cont.amount_remaining:
            updates['amount_remaining'] = float(amount_remaining)

        if updates:
            contract_controller.update_contract(
                current_user, contract_id, **updates)
            console.print(
                "[bold green][OK]Contrat mis à jour avec succès!"
                "[/bold green]")
        else:
            console.print(
                "[yellow]Aucune modification effectuée[/yellow]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@contract.command('sign')
@click.argument('contract_id', type=int)
def contract_sign(contract_id):
    """Signer un contrat"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        contract_controller = ContractController(db)
        cont = contract_controller.sign_contract(
            current_user, contract_id)

        console.print(
            f"[bold green][OK]Contrat {cont.contract_number} signé "
            f"avec succès![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


# ===== COMMANDES ÉVÉNEMENTS =====

@cli.group()
def event():
    """Gestion des événements"""
    pass


@event.command('create')
def event_create():
    """Créer un nouvel événement"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        contract_id = int(Prompt.ask("ID du contrat"))
        event_name = Prompt.ask("Nom de l'événement")
        location = Prompt.ask("Lieu")
        attendees = int(Prompt.ask("Nombre de participants"))

        # Parser les dates au format YYYY-MM-DD HH:MM
        start_date_str = Prompt.ask("Date de début (YYYY-MM-DD HH:MM)")
        end_date_str = Prompt.ask("Date de fin (YYYY-MM-DD HH:MM)")

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")

        # Les notes sont optionnelles : une chaîne vide devient None
        notes = Prompt.ask("Notes (optionnel)", default="")

        event_controller = EventController(db)
        evt = event_controller.create_event(
            current_user,
            contract_id,
            event_name,
            start_date,
            end_date,
            location,
            attendees,
            notes if notes else None
        )

        console.print(
            f"[bold green][OK]Événement {evt.event_name} créé "
            f"avec succès![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@event.command('list')
@click.option('--mine', is_flag=True,
              help="Afficher uniquement mes événements")
@click.option('--no-support', is_flag=True,
              help="Afficher uniquement les événements sans support")
def event_list(mine, no_support):
    """Lister les événements"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        event_controller = EventController(db)

        # --mine : usage Support pour voir ses propres événements
        # --no-support : usage Gestion pour les événements à assigner
        if mine:
            events = event_controller.get_my_events(current_user)
            title = "Mes Événements"
        elif no_support:
            events = event_controller.get_events_without_support(
                current_user)
            title = "Événements Sans Support"
        else:
            events = event_controller.get_all_events(current_user)
            title = "Liste des Événements"

        table = Table(title=title)
        table.add_column("ID", style="cyan")
        table.add_column("Nom", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("Lieu", style="blue")
        table.add_column("Participants", style="magenta")
        table.add_column("Support", style="red")

        for evt in events:
            if evt.support_contact:
                support_name = evt.support_contact.full_name
            else:
                support_name = "Non assigné"
            table.add_row(
                str(evt.id),
                evt.event_name,
                evt.event_date_start.strftime("%Y-%m-%d %H:%M"),
                evt.location,
                str(evt.attendees),
                support_name
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@event.command('update')
@click.argument('event_id', type=int)
def event_update(event_id):
    """Mettre à jour un événement"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        event_controller = EventController(db)
        evt = event_controller.get_event_by_id(current_user, event_id)

        if not evt:
            console.print(
                f"[bold red][X]Événement {event_id} non trouvé"
                f"[/bold red]")
            return

        console.print(f"Modification de: {evt.event_name}")

        # Pré-remplir avec les valeurs actuelles
        event_name = Prompt.ask("Nouveau nom", default=evt.event_name)
        location = Prompt.ask("Nouveau lieu", default=evt.location)
        attendees = Prompt.ask(
            "Nouveau nombre de participants",
            default=str(evt.attendees))
        # Les notes peuvent être None en base ; chaîne vide par défaut
        notes = Prompt.ask("Nouvelles notes", default=evt.notes or "")

        # N'envoyer au controller que les champs réellement modifiés
        updates = {}
        if event_name != evt.event_name:
            updates['event_name'] = event_name
        if location != evt.location:
            updates['location'] = location
        if int(attendees) != evt.attendees:
            updates['attendees'] = int(attendees)
        if notes != (evt.notes or ""):
            updates['notes'] = notes

        if updates:
            event_controller.update_event(
                current_user, event_id, **updates)
            console.print(
                "[bold green][OK]Événement mis à jour avec succès!"
                "[/bold green]")
        else:
            console.print(
                "[yellow]Aucune modification effectuée[/yellow]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


@event.command('assign-support')
@click.argument('event_id', type=int)
@click.argument('support_id', type=int)
def event_assign_support(event_id, support_id):
    """Assigner un membre du support à un événement"""
    db = SessionLocal()
    try:
        auth_controller = AuthController(db)
        current_user = auth_controller.require_auth()

        event_controller = EventController(db)
        evt = event_controller.assign_support(
            current_user, event_id, support_id)

        console.print(
            f"[bold green][OK]Support assigné à l'événement "
            f"{evt.event_name}![/bold green]")

    except Exception as e:
        console.print(f"[bold red][X] Erreur: {str(e)}[/bold red]")
    finally:
        db.close()


if __name__ == '__main__':
    cli()
