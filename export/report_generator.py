"""تولید گزارش‌های هوشمند و تحلیلی"""

from datetime import datetime
from typing import List
import math
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from core import Motor, Project, COMPONENT_LABELS, COLORS


class ReportGenerator:
    """تولید گزارش‌های مختلف"""
    
    def __init__(self, app):
        self.app = app
    
    def generate_smart_report(self):
        """تولید گزارش هوشمند"""
        project = self.app.get_current_project()
        if not project:
            messagebox.showwarning("Warning", "No project selected!")
            return
        
        # ✅ دریافت Current Revision
        current_revision = project.get_current_revision()
        revision_name = current_revision.name if current_revision else "Rev-0"
        
        devices = project.get_all_devices()
        if not devices:
            messagebox.showwarning("Warning", "No devices found!")
            return
        
        report_type = self._select_report_type()
        if not report_type:
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Smart Report",
            # ✅ نام فایل شامل Revision
            initialfile=f"Smart_Report_{project.name}_{revision_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )
        
        if not file_path:
            return
                
        if report_type == "summary":
            content = self._generate_summary_report(project, devices)
        elif report_type == "analysis":
            content = self._generate_analysis_report(project, devices)
        elif report_type == "full":
            content = self._generate_full_report(project, devices)
        else:
            return
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
        self._show_report_preview(content)
    
    def _select_report_type(self) -> str:
        from tkinter import simpledialog
        
        types = {
            "1": ("summary", "📊 Summary Report - خلاصه کلی"),
            "2": ("analysis", "📈 Analysis Report - تحلیل کامپوننت‌ها"),
            "3": ("full", "📋 Full Report - گزارش کامل")
        }
        
        options = "\n".join([f"{key}. {desc}" for key, (_, desc) in types.items()])
        
        choice = simpledialog.askstring(
            "Select Report Type",
            f"Choose report type:\n\n{options}\n\nEnter number (1-3):"
        )
        
        if choice and choice in types:
            return types[choice][0]
        return None
    
    def _generate_summary_report(self, project: Project, devices: List[Motor]) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("PROJECT SUMMARY REPORT")
        lines.append("=" * 60)
        lines.append(f"Project: {project.name}")
        lines.append(f"Generated: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        
        stats = project.get_statistics()
        lines.append("📊 OVERALL STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Total Sections: {stats['total_sections']}")
        lines.append(f"Total Devices: {stats['total_devices']}")
        lines.append(f"Active Devices: {stats['active_devices']}")
        lines.append(f"Inactive Devices: {stats['inactive_devices']}")
        lines.append("")
        lines.append("📈 I/O STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Digital Inputs (DI): {stats['total_di']}")
        lines.append(f"Digital Outputs (DO): {stats['total_do']}")
        lines.append(f"Analog Inputs (AI): {stats['total_ai']}")
        lines.append(f"Analog Outputs (AO): {stats['total_ao']}")
        lines.append(f"Total I/O: {stats['total_io']}")
        lines.append("")
        
        total_io = stats['total_io']
        cbx = math.ceil(total_io / 64) if total_io > 0 else 0
        fbx = max(0, math.ceil(total_io / 16) - 1) if total_io > 0 else 0
        
        lines.append("🎛️ CONTROLLER REQUIREMENTS")
        lines.append("-" * 40)
        lines.append(f"ABB CBX-8R8: {cbx} units (64 I/O each)")
        lines.append(f"ABB FBX-8R8: {fbx} units (16 I/O each)")
        lines.append("")
        
        lines.append("📁 SECTIONS BREAKDOWN")
        lines.append("-" * 40)
        for section in project.sections:
            section_stats = section.get_statistics()
            lines.append(f"\n{section.name}:")
            lines.append(f"  Devices: {section_stats['device_count']}")
            lines.append(f"  Total I/O: {section_stats['total_io']}")
            if stats['total_io'] > 0:
                pct = (section_stats['total_io'] / stats['total_io'] * 100)
                lines.append(f"  Percentage: {pct:.1f}%")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("End of Report")
        return "\n".join(lines)
    
    def _generate_analysis_report(self, project: Project, devices: List[Motor]) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("COMPONENT ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"Project: {project.name}")
        lines.append(f"Generated: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append("🔧 COMPONENT USAGE ANALYSIS")
        lines.append("-" * 40)
        
        usage = {}
        for device in devices:
            for field in COMPONENT_LABELS.keys():
                qty = getattr(device, field, 0)
                if qty > 0:
                    usage[field] = usage.get(field, 0) + qty
        
        if usage:
            sorted_usage = sorted(usage.items(), key=lambda x: x[1], reverse=True)
            lines.append(f"{'Component':<30} {'Quantity':>10} {'Percentage':>10}")
            lines.append("-" * 50)
            total_components = sum(usage.values())
            for field, qty in sorted_usage:
                label = COMPONENT_LABELS.get(field, {}).get('en', field)
                pct = (qty / total_components * 100) if total_components > 0 else 0
                lines.append(f"{label:<30} {qty:>10} {pct:>9.1f}%")
            lines.append("-" * 50)
            lines.append(f"{'TOTAL':<30} {total_components:>10} 100.0%")
        else:
            lines.append("No components found in the project.")
        
        lines.append("")
        lines.append("📊 DEVICE COMPLEXITY ANALYSIS")
        lines.append("-" * 40)
        
        simple = medium = complex = 0
        for device in devices:
            total = device.get_total_io()
            if total <= 5:
                simple += 1
            elif total <= 15:
                medium += 1
            else:
                complex += 1
        
        lines.append(f"Simple (I/O ≤ 5): {simple} devices")
        lines.append(f"Medium (5 < I/O ≤ 15): {medium} devices")
        lines.append(f"Complex (I/O > 15): {complex} devices")
        
        if devices:
            avg_io = sum(d.get_total_io() for d in devices) / len(devices)
            lines.append(f"Average I/O per device: {avg_io:.1f}")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("End of Report")
        return "\n".join(lines)
    
    def _generate_full_report(self, project: Project, devices: List[Motor]) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("FULL PROJECT REPORT")
        lines.append("=" * 70)
        lines.append(f"Project: {project.name}")
        lines.append(f"Generated: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
        lines.append("=" * 70)
        lines.append("")
        
        lines.append("📋 PROJECT INFORMATION")
        lines.append("-" * 40)
        lines.append(f"Client: {project.client_name or 'Not specified'}")
        lines.append(f"Client Phone: {project.client_phone or 'Not specified'}")
        lines.append(f"Client Address: {project.client_address or 'Not specified'}")
        lines.append("")
        lines.append(f"Consultant: {project.consultant_name or 'Not specified'}")
        lines.append(f"Consultant Phone: {project.consultant_phone or 'Not specified'}")
        lines.append("")
        lines.append(f"Contractor: {project.contractor_name or 'Not specified'}")
        lines.append(f"Designer: {project.designer_name or 'Not specified'}")
        lines.append("")
        
        stats = project.get_statistics()
        lines.append("📊 STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Total Sections: {stats['total_sections']}")
        lines.append(f"Total Devices: {stats['total_devices']}")
        lines.append(f"Active Devices: {stats['active_devices']}")
        lines.append("")
        lines.append(f"DI: {stats['total_di']}")
        lines.append(f"DO: {stats['total_do']}")
        lines.append(f"AI: {stats['total_ai']}")
        lines.append(f"AO: {stats['total_ao']}")
        lines.append(f"Total I/O: {stats['total_io']}")
        lines.append("")
        
        lines.append("📁 SECTIONS DETAILS")
        lines.append("-" * 40)
        for section in project.sections:
            lines.append(f"\n{'='*40}")
            lines.append(f"Section: {section.name}")
            if section.description:
                lines.append(f"Description: {section.description}")
            lines.append("-" * 40)
            if section.devices:
                lines.append(f"{'#':<4} {'Device Name':<25} {'DI':<4} {'DO':<4} {'AI':<4} {'AO':<4} {'Total':<6}")
                lines.append("-" * 55)
                for i, motor in enumerate(section.devices, 1):
                    total = motor.get_total_io()
                    name = motor.Name or f"Device_{i}"
                    lines.append(f"{i:<4} {name:<25} {motor.DI:<4} {motor.DO:<4} {motor.AI:<4} {motor.AO:<4} {total:<6}")
                section_io = section.get_total_io()
                lines.append("-" * 55)
                lines.append(f"{'Section Total:':<33} {section_io:>6}")
            else:
                lines.append("No devices in this section.")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append("End of Report")
        return "\n".join(lines)
    
    def _show_report_preview(self, content: str):
        win = tk.Toplevel(self.app.root)
        win.title("📄 Report Preview")
        win.geometry("800x600")
        win.transient(self.app.root)
        
        text_area = scrolledtext.ScrolledText(win, wrap="none", font=("Courier New", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, content)
        text_area.config(state="disabled")
        
        tk.Button(win, text="Close", command=win.destroy,
                  bg=COLORS['danger'], fg=COLORS['white'],
                  font=("Segoe UI", 10, "bold"), relief='flat',
                  padx=20, pady=5).pack(pady=10)