import os
from sqlalchemy.orm import Session
from pathlib import Path
from backend.models.database_models import TARAFinding, AuditLog
import datetime

class ReportService:
    @staticmethod
    def generate_report(db: Session, project_id: int, format: str = "markdown"):
        reports_dir = Path("c:/TARA/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        findings = db.query(TARAFinding).filter_by(project_id=project_id).all()
        
        filename = f"tara_report_{project_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        filepath = reports_dir / filename
        
        with open(filepath, "w") as f:
            f.write(f"# TARA Report for Project {project_id}\n\n")
            f.write(f"Generated at: {datetime.datetime.now()}\n\n")
            
            f.write("## Findings\n\n")
            for finding in findings:
                f.write(f"### {finding.title} ({finding.finding_type})\n")
                f.write(f"{finding.description}\n\n")
                
        log = AuditLog(project_id=project_id, action="report_generation", details=f"Generated {filename}")
        db.add(log)
        db.commit()
        
        return filename
