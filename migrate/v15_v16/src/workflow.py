"""
Workflow Management System
Timeline-based phase tracking với horizontal roadmap display
"""
import time
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import click


class StepStatus(Enum):
    """Status của từng step trong workflow"""
    PENDING = "⏳"
    RUNNING = "🔄"
    COMPLETED = "✅"
    FAILED = "❌"
    SKIPPED = "⏭️"


@dataclass
class WorkflowStep:
    """Định nghĩa một step trong workflow"""
    id: str
    name: str
    description: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None


class WorkflowTracker:
    """
    Workflow tracker với timeline visualization
    Hiển thị các phase theo hàng ngang (horizontal roadmap)
    """

    def __init__(self, workflow_name: str, steps: List[WorkflowStep]):
        self.workflow_name = workflow_name
        self.steps = {step.id: step for step in steps}
        self.step_order = [step.id for step in steps]
        self.current_step_index = 0
        self.workflow_start_time = None
        self.workflow_end_time = None
        self.is_running = False

    def start_workflow(self):
        """Bắt đầu workflow"""
        self.workflow_start_time = time.time()
        self.is_running = True
        click.echo(f"\n🚀 Starting {self.workflow_name}")
        self.show_horizontal_roadmap()

    def show_horizontal_roadmap(self):
        """Hiển thị roadmap theo hàng ngang (timeline)"""
        click.echo("\n" + "=" * 80)
        click.echo(f"📋 {self.workflow_name} - Timeline Roadmap")
        click.echo("=" * 80)

        # Header với số thứ tự
        header = "    "
        for i, step_id in enumerate(self.step_order, 1):
            header += f"{i:^12}"
        click.echo(header)

        # Timeline với tên steps
        timeline = "    "
        for step_id in self.step_order:
            step = self.steps[step_id]
            timeline += f"{step.name[:10]:^12}"
        click.echo(timeline)

        # Status line với icons
        status_line = "    "
        for step_id in self.step_order:
            step = self.steps[step_id]
            status_line += f"{step.status.value:^12}"
        click.echo(status_line)

        # Connection line
        connection = "    "
        for i, step_id in enumerate(self.step_order):
            if i == 0:
                connection += "●───────────"
            elif i == len(self.step_order) - 1:
                connection += "─────────●"
            else:
                connection += "─────●──────"
        click.echo(connection)

        click.echo("=" * 80)

    def show_compact_progress(self):
        """Hiển thị progress compact"""
        completed = sum(1 for step in self.steps.values()
                        if step.status == StepStatus.COMPLETED)
        failed = sum(1 for step in self.steps.values()
                     if step.status == StepStatus.FAILED)
        total = len(self.steps)

        progress_bar = ""
        for step_id in self.step_order:
            step = self.steps[step_id]
            if step.status == StepStatus.COMPLETED:
                progress_bar += "█"
            elif step.status == StepStatus.RUNNING:
                progress_bar += "▓"
            elif step.status == StepStatus.FAILED:
                progress_bar += "▒"
            else:
                progress_bar += "░"

        percentage = int((completed / total) * 100) if total > 0 else 0

        click.echo(
            f"\n📊 Progress: [{progress_bar}] {percentage}% ({completed}/{total})")
        if failed > 0:
            click.echo(f"⚠️  Failed steps: {failed}")

    def start_step(self, step_id: str):
        """Bắt đầu một step"""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step = self.steps[step_id]
        step.status = StepStatus.RUNNING
        step.start_time = time.time()

        click.echo(f"\n🔄 Starting: {step.name}")
        click.echo(f"   {step.description}")

    def complete_step(self, step_id: str, message: Optional[str] = None):
        """Hoàn thành một step"""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step = self.steps[step_id]
        step.status = StepStatus.COMPLETED
        step.end_time = time.time()

        duration = step.end_time - step.start_time if step.start_time else 0

        click.echo(f"✅ Completed: {step.name} ({duration:.1f}s)")
        if message:
            click.echo(f"   {message}")

    def fail_step(self, step_id: str, error_message: str):
        """Fail một step"""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step = self.steps[step_id]
        step.status = StepStatus.FAILED
        step.end_time = time.time()
        step.error_message = error_message

        click.echo(f"❌ Failed: {step.name}")
        click.echo(f"   Error: {error_message}")

    def skip_step(self, step_id: str, reason: str = "Skipped"):
        """Skip một step"""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step = self.steps[step_id]
        step.status = StepStatus.SKIPPED
        step.end_time = time.time()

        click.echo(f"⏭️  Skipped: {step.name} - {reason}")

    def finish_workflow(self, show_summary: bool = True):
        """Kết thúc workflow"""
        self.workflow_end_time = time.time()
        self.is_running = False

        if show_summary:
            self.show_summary()

    def show_summary(self):
        """Hiển thị tổng kết workflow"""
        click.echo("\n" + "=" * 80)
        click.echo(f"📋 {self.workflow_name} - Summary Report")
        click.echo("=" * 80)

        completed = [s for s in self.steps.values() if s.status ==
                     StepStatus.COMPLETED]
        failed = [s for s in self.steps.values() if s.status ==
                  StepStatus.FAILED]
        skipped = [s for s in self.steps.values() if s.status ==
                   StepStatus.SKIPPED]

        total_time = (self.workflow_end_time -
                      self.workflow_start_time) if self.workflow_start_time else 0

        click.echo(f"⏱️  Total time: {total_time:.1f}s")
        click.echo(f"✅ Completed: {len(completed)}/{len(self.steps)}")
        click.echo(f"❌ Failed: {len(failed)}")
        click.echo(f"⏭️  Skipped: {len(skipped)}")

        if failed:
            click.echo("\n❌ Failed Steps:")
            for step in failed:
                click.echo(f"   • {step.name}: {step.error_message}")

        if completed:
            click.echo("\n✅ Completed Steps:")
            for step in completed:
                duration = (
                    step.end_time - step.start_time) if step.start_time and step.end_time else 0
                click.echo(f"   • {step.name} ({duration:.1f}s)")

        click.echo("=" * 80)

    def show_roadmap(self):
        """Hiển thị roadmap trước khi bắt đầu"""
        click.echo(f"\n📋 {self.workflow_name} - Roadmap Preview")
        click.echo("─" * 60)

        for i, step_id in enumerate(self.step_order, 1):
            step = self.steps[step_id]
            click.echo(f"{i:2d}. {step.name}")
            click.echo(f"    {step.description}")

        click.echo("─" * 60)

    def get_status(self) -> Dict:
        """Lấy trạng thái hiện tại"""
        completed = sum(1 for s in self.steps.values()
                        if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps.values()
                     if s.status == StepStatus.FAILED)

        return {
            "workflow_name": self.workflow_name,
            "is_running": self.is_running,
            "total_steps": len(self.steps),
            "completed": completed,
            "failed": failed,
            "progress_percentage": int((completed / len(self.steps)) * 100) if self.steps else 0,
            "current_step": self.step_order[self.current_step_index] if self.current_step_index < len(self.step_order) else None
        }


# Pre-defined workflows
def create_health_check_workflow() -> WorkflowTracker:
    """Tạo workflow cho health check"""
    steps = [
        WorkflowStep("python", "Python",
                     "Check Python version and environment"),
        WorkflowStep("deps", "Dependencies", "Verify required packages"),
        WorkflowStep("postgres", "PostgreSQL", "Test database connection"),
        WorkflowStep("odoo_v15", "Odoo v15", "Check v15 instance"),
        WorkflowStep("odoo_v16", "Odoo v16", "Check v16 instance"),
        WorkflowStep("odoo_v17", "Odoo v17", "Check v17 instance"),
        WorkflowStep("odoo_v18", "Odoo v18", "Check v18 instance"),
    ]
    return WorkflowTracker("Health Check", steps)


def create_migration_workflow() -> WorkflowTracker:
    """Tạo workflow cho migration process"""
    steps = [
        WorkflowStep("pre_check", "Pre-check", "Pre-flight system check"),
        WorkflowStep("backup", "Backup", "Backup source database and files"),
        WorkflowStep("schema_migration", "Schema", "Migrate database schema"),
        WorkflowStep("data_migration", "Data", "Migrate data and records"),
        WorkflowStep("post_check", "Post-check", "Verify migration results"),
        WorkflowStep("cleanup", "Cleanup", "Clean up temporary files"),
    ]
    return WorkflowTracker("Migration v15 → v16", steps)


def create_setup_workflow() -> WorkflowTracker:
    """Tạo workflow cho setup process"""
    steps = [
        WorkflowStep("docker_check", "Docker", "Check Docker environment"),
        WorkflowStep("network_setup", "Network",
                     "Setup network infrastructure"),
        WorkflowStep("postgres_setup", "PostgreSQL", "Setup database server"),
        WorkflowStep("odoo_v15_setup", "Odoo v15", "Setup Odoo v15 instance"),
        WorkflowStep("odoo_v16_setup", "Odoo v16", "Setup Odoo v16 instance"),
        WorkflowStep("init_data", "Init Data", "Initialize demo data"),
        WorkflowStep("verification", "Verify", "Verify setup completion"),
    ]
    return WorkflowTracker("Environment Setup", steps)


def execute_with_progress(func, *args, **kwargs):
    """Utility function để execute với progress indication"""
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        return False, str(e)
