import os
from django.core.management.base import BaseCommand, CommandError
from core.services.esocial_services import export_esocial_backup, import_esocial_backup


class Command(BaseCommand):
    help = "Exporta ou importa arquivos de backup e XMLs do eSocial para o sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--export",
            type=str,
            nargs="?",
            const="backup_esocial.zip",
            help="Caminho do arquivo ZIP de destino para exportação do backup do eSocial.",
        )
        parser.add_argument(
            "--import",
            dest="import_files",
            type=str,
            nargs="+",
            help="Caminho de um ou mais arquivos ZIP ou XML do eSocial para importação e consolidação.",
        )

    def handle(self, *args, **options):
        export_path = options.get("export")
        import_files = options.get("import_files")

        if not export_path and not import_files:
            raise CommandError("Informe --export [caminho] ou --import <caminho1> [caminho2...].")

        if export_path:
            self.stdout.write(self.style.NOTICE(f"Exportando backup do eSocial para: {export_path}"))
            zip_bytes, default_filename = export_esocial_backup()
            dest = export_path if export_path != "backup_esocial.zip" else default_filename
            with open(dest, "wb") as f:
                f.write(zip_bytes)
            self.stdout.write(
                self.style.SUCCESS(f"Backup exportado com sucesso para '{dest}' ({len(zip_bytes)} bytes).")
            )

        if import_files:
            files_payload = []
            for path in import_files:
                if not os.path.exists(path):
                    raise CommandError(f"Arquivo não encontrado: '{path}'.")
                with open(path, "rb") as f:
                    files_payload.append((f.read(), os.path.basename(path)))

            self.stdout.write(
                self.style.NOTICE(f"Importando eventos do eSocial a partir de {len(files_payload)} arquivo(s)...")
            )
            result = import_esocial_backup(files_payload)
            if result.get("count", 0) > 0:
                self.stdout.write(self.style.SUCCESS(result.get("message", "Sucesso.")))
            else:
                self.stdout.write(self.style.WARNING(result.get("message", "Nenhum registro importado.")))

