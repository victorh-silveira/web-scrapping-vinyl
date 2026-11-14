"""CLI entrypoint for Amazon BR Vinyl Smart Scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from vinyl_scraper.application.dto import RunAnalysisResult
from vinyl_scraper.application.use_cases import ScrapeAndAnalyzeVinylsUseCase
from vinyl_scraper.domain.entities import AlbumSearchReport, VinylQuery
from vinyl_scraper.infrastructure.external.null_external_history import NullExternalPriceHistory
from vinyl_scraper.infrastructure.io.json_catalog_reader import JsonCatalogReader
from vinyl_scraper.infrastructure.io.json_report_exporter import JsonReportExporter
from vinyl_scraper.infrastructure.persistence.sqlite_price_history_repo import (
    SqlitePriceHistoryRepository,
)
from vinyl_scraper.infrastructure.scrapers.playwright_amazon_scraper import PlaywrightAmazonScraper

app = typer.Typer(
    name="vinyl-scraper",
    help="WebScraper inteligente de discos de vinil na Amazon BR.",
    no_args_is_help=True,
)
console = Console()


def _parse_optional_date(raw: str | None) -> date | None:
    return date.fromisoformat(raw) if raw else None


def _render_console_summary(result: RunAnalysisResult) -> None:
    for report in result.reports:
        title = f"{report.query.artist} - {report.query.album}"
        if report.blocked:
            console.print(f"[bold red]BLOQUEADO[/bold red] {title}: {report.error_message}")
            continue

        table = Table(title=f"Vinis encontrados: {title} ({len(report.editions)} versões)")
        table.add_column("Artista - Álbum", style="cyan")
        table.add_column("Versão / Edição", style="white")
        table.add_column("Atual", justify="right", style="green")
        table.add_column("Média", justify="right")
        table.add_column("Mediana", justify="right")
        table.add_column("Pré-BF", justify="right")
        table.add_column("BF", justify="right")
        table.add_column("Desc. %", justify="right")
        table.add_column("Custo/Benef.", justify="right", style="bold magenta")
        table.add_column("Veredito", style="yellow")

        for ed in report.editions:
            pre_bf = (
                str(ed.bf_comparison.pre_bf_last_price)
                if ed.bf_comparison.pre_bf_last_price
                else "-"
            )
            bf_val = str(ed.bf_comparison.bf_price) if ed.bf_comparison.bf_price else "-"
            discount_pct = (
                ed.bf_comparison.discount_vs_median_pct
                if ed.bf_comparison.discount_vs_median_pct != 0
                else ed.bf_comparison.discount_vs_pre_bf_pct
            )
            table.add_row(
                title,
                ed.edition_info.edition_label,
                str(ed.current_price),
                str(ed.stats.mean_price),
                str(ed.stats.median_price),
                pre_bf,
                bf_val,
                f"{discount_pct}%",
                f"{ed.cost_benefit.total_score:.1f}",
                ed.bf_comparison.deal_verdict,
            )

        console.print(table)

    console.print(f"\n[bold green]Relatório JSON salvo em:[/bold green] {result.output_path}")


def _execute_pipeline(
    input_path: Path,
    output_path: Path,
    db_path: Path,
    max_pages: int,
    headless: bool,
    scrape: bool,
    bf_start: str | None,
    bf_end: str | None,
    pre_bf_days: int | None,
) -> None:
    reader = JsonCatalogReader(
        path=input_path,
        bf_start_override=_parse_optional_date(bf_start),
        bf_end_override=_parse_optional_date(bf_end),
        pre_bf_days_override=pre_bf_days,
    )
    repo = SqlitePriceHistoryRepository(db_path=db_path)
    scraper = PlaywrightAmazonScraper(headless=headless)
    external = NullExternalPriceHistory()
    exporter = JsonReportExporter(output_path=output_path)

    try:
        use_case = ScrapeAndAnalyzeVinylsUseCase(
            catalog_reader=reader,
            scraper=scraper,
            history_repo=repo,
            external_history=external,
            exporter=exporter,
        )
        action_label = "Buscando" if scrape else "Analisando"
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(f"{action_label} vinis...", total=None)

            def _on_progress(
                idx: int, total: int, query: VinylQuery, report: AlbumSearchReport | None
            ) -> None:
                label = f"{query.artist} - {query.album}"
                if report is None:
                    progress.update(
                        task_id,
                        total=total,
                        completed=idx - 1,
                        description=f"[cyan]{action_label}:[/cyan] {label}",
                    )
                    return
                if report.blocked:
                    progress.console.print(
                        f"[red][BLOQUEADO][/red] {label}: {report.error_message}"
                    )
                else:
                    progress.console.print(
                        f"[green][OK][/green] {label}: {len(report.editions)} versões"
                    )
                progress.update(task_id, total=total, completed=idx)

            result = use_case.execute(max_pages=max_pages, scrape=scrape, on_progress=_on_progress)
        _render_console_summary(result)
    finally:
        repo.close()


@app.command("run")
def run_command(
    input_file: Annotated[
        Path, typer.Option("--input", "-i", exists=True, help="JSON de discos.")
    ] = Path("data/vinyls.json"),
    output_file: Annotated[Path, typer.Option("--output", "-o", help="JSON de saída.")] = Path(
        "output/report.json"
    ),
    db_file: Annotated[Path, typer.Option("--db", help="Banco SQLite de histórico.")] = Path(
        "data/price_history.db"
    ),
    max_pages: Annotated[
        int, typer.Option("--max-pages", min=1, max=10, help="Páginas por busca.")
    ] = 2,
    headless: Annotated[
        bool, typer.Option("--headless/--no-headless", help="Modo headless.")
    ] = True,
    bf_start: Annotated[
        str | None, typer.Option("--bf-start", help="Início Black Friday (YYYY-MM-DD).")
    ] = None,
    bf_end: Annotated[
        str | None, typer.Option("--bf-end", help="Fim Black Friday (YYYY-MM-DD).")
    ] = None,
    pre_bf_days: Annotated[
        int | None, typer.Option("--pre-bf-days", help="Dias pré-Black Friday.")
    ] = None,
) -> None:
    """Busca todas as versões na Amazon BR, atualiza histórico e gera o ranking."""
    _execute_pipeline(
        input_path=input_file,
        output_path=output_file,
        db_path=db_file,
        max_pages=max_pages,
        headless=headless,
        scrape=True,
        bf_start=bf_start,
        bf_end=bf_end,
        pre_bf_days=pre_bf_days,
    )


@app.command("analyze")
def analyze_command(
    input_file: Annotated[
        Path, typer.Option("--input", "-i", exists=True, help="JSON de discos.")
    ] = Path("data/vinyls.json"),
    output_file: Annotated[Path, typer.Option("--output", "-o", help="JSON de saída.")] = Path(
        "output/report.json"
    ),
    db_file: Annotated[Path, typer.Option("--db", help="Banco SQLite de histórico.")] = Path(
        "data/price_history.db"
    ),
    bf_start: Annotated[
        str | None, typer.Option("--bf-start", help="Início Black Friday (YYYY-MM-DD).")
    ] = None,
    bf_end: Annotated[
        str | None, typer.Option("--bf-end", help="Fim Black Friday (YYYY-MM-DD).")
    ] = None,
    pre_bf_days: Annotated[
        int | None, typer.Option("--pre-bf-days", help="Dias pré-Black Friday.")
    ] = None,
) -> None:
    """Reanalisa estatísticas e custo-benefício usando apenas o histórico salvo no SQLite."""
    _execute_pipeline(
        input_path=input_file,
        output_path=output_file,
        db_path=db_file,
        max_pages=1,
        headless=True,
        scrape=False,
        bf_start=bf_start,
        bf_end=bf_end,
        pre_bf_days=pre_bf_days,
    )


if __name__ == "__main__":
    app()
