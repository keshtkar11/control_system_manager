# ai/local_proposal_generator.py
"""
تولید پروپوزال محلی — بدون نیاز به AI خارجی

نسخه 3.0 — اصلاح‌شده
- ✅ رفع self.importer با lazy loading
- ✅ fallback کامل برای قالب‌های نبوده
- ✅ نمایش تصاویر (اگر فایل‌ها موجود باشند)
- ✅ LOM گروه‌بندی‌شده
- ✅ کنترلرها بر اساس I/O واقعی
- ✅ Section I/O List با total صحیح
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from utils.paths import get_resource_path
from core.constants import (
    COMPONENT_LABELS,
    IO_CALCULATION,
    gregorian_to_jalali,
)

from ai.proposal_section_detector import ProposalSectionDetector

logger = logging.getLogger(__name__)


class LocalProposalGenerator:
    """
    تولید پروپوزال محلی از داده‌های پروژه
    """
    
    # ================================================================
    # INIT
    # ================================================================
    
    def __init__(self, db_manager, app):
        self.db = db_manager
        self.app = app
        self.detector = ProposalSectionDetector()
        
        # ✅ Lazy import برای جلوگیری از circular import
        self._importer = None
        
        # ===== مسیرها =====
        self.template_dir = get_resource_path("ai")
        self.templates_dir = get_resource_path("ai", "proposal_templates")
        self.images_dir = get_resource_path("ai", "proposal_images")
        
        # ===== اطلاعات شرکت =====
        self.company_name = "Vahhaj Sanat Energy Co."
        self.company_name_fa = "وهاج صنعت انرژی"
        self.designer_name = "Mr. Keshtkar"
        
        # ===== تصاویر هر سکشن =====
        self.section_images = {
            # ===== تصاویر اصلی =====
            'boiler': 'boiler.png',
            'chiller': 'chiller.png',
            'primary_loop': 'primary_loop.png',
            'secondary_loop': 'secondary_loop.png',
            'dhw': 'dhw.png',
            'ahu': 'ahu.png',
            'booster_pump': 'booster_pump.png',
            'expansion_tank': 'expansion_tank.png',
            'hardware': 'hardware.png',
            'panel': 'Panel.png',
            
            # ===== تصاویر جدید (اگر بسازید) =====
            'mechanical_room': 'mechanical_room.png',  # ← باید فایل اضافه شود
            'exhaust_fan': 'exhaust_fan.png',          # ← باید فایل اضافه شود
            'building': 'building.png',                # ← باید فایل اضافه شود
            'fan': 'fan.png',                          # ← باید فایل اضافه شود
            'pump': 'pump.png',                        # ← باید فایل اضافه شود
        }
    
    @property
    def importer(self):
        """✅ Lazy loading برای importer"""
        if self._importer is None:
            try:
                from ai.proposal_importer import ProposalImporter
                self._importer = ProposalImporter(self.db, self.app)
                logger.debug("✅ ProposalImporter loaded")
            except Exception as e:
                logger.warning(f"⚠️ Could not load ProposalImporter: {e}")
                self._importer = None
        return self._importer
    
    # ================================================================
    # MAIN ENTRY
    # ================================================================
    
    def generate(self, project, revision_name: str = None) -> str:
        """تولید پروپوزال کامل"""
        try:
            # ===== رویژن =====
            if revision_name:
                revision = project.get_revision_by_name(revision_name)
            else:
                revision = project.get_current_revision()
            
            if not revision:
                return "❌ رویژن یافت نشد."
            
            logger.info(f"📄 Generating proposal for '{project.name}' / '{revision.name}'")
            
            # ===== داده‌های پروژه =====
            project_data = self._collect_project_data(project, revision)
            
            if not project_data.get('devices'):
                return "❌ پروژه هیچ دستگاهی ندارد. ابتدا دستگاه‌ها را اضافه کنید."
            
            # ===== گروه‌بندی سکشن‌ها =====
            sections_by_type = self.detector.group_sections_by_type(revision.sections)
            
            # ===== ساخت متن =====
            parts = []
            
            # ۱. صفحه عنوان
            parts.append(self._build_title_page(project, revision, project_data))
            
            # ۲. فهرست مطالب
            parts.append(self._build_table_of_contents(sections_by_type))
            
            # ۳. معرفی پروژه
            parts.append(self._build_intro(project, revision, project_data))
            
            # ۴. معماری سیستم
            parts.append(self._build_architecture(project_data))
            
            # ۵. بخش‌های تخصصی
            for section_type, sections in sections_by_type.items():
                if section_type == '_unknown':
                    continue
                parts.append(self._build_section_content(
                    section_type, sections, project_data
                ))
            
            # ۶. لیست کامل I/O
            parts.append(self._build_io_list(project_data))
            
            # ۷. مشخصات کنترلرها
            parts.append(self._build_controller_requirements(project_data))
            
            # ۸. لیست مواد (LOM)
            parts.append(self._build_lom(project_data))
            
            # ۹. پایان
            parts.append(self._build_footer(project, revision))
            
            result = "\n\n".join(parts)
            logger.info(f"✅ Proposal generated: {len(result)} chars")
            return result
        
        except Exception as e:
            logger.error(f"Error generating proposal: {e}", exc_info=True)
            return f"❌ خطا در تولید پروپوزال: {e}"
    
    def generate_section_only(
        self,
        project,
        revision_name: str,
        section_type: str,
    ) -> str:
        """تولید پروپوزال فقط برای یک سکشن"""
        try:
            revision = project.get_revision_by_name(revision_name)
            if not revision:
                return f"❌ رویژن '{revision_name}' یافت نشد."
            
            sections_by_type = self.detector.group_sections_by_type(revision.sections)
            
            if section_type not in sections_by_type:
                return f"❌ سکشن '{section_type}' در این پروژه یافت نشد."
            
            project_data = self._collect_project_data(project, revision)
            sections = sections_by_type[section_type]
            
            parts = []
            
            # ۱. صفحه عنوان
            parts.append(self._build_title_page(project, revision, project_data))
            
            # ۲. محتوای سکشن
            parts.append(self._build_section_content(
                section_type, sections, project_data
            ))
            
            # ۳. I/O این سکشن
            parts.append(self._build_section_io_list(sections, project_data))
            
            # ۴. پایان
            parts.append(self._build_footer(project, revision))
            
            return "\n\n".join(parts)
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return f"❌ خطا: {e}"
    
    # ================================================================
    # DATA COLLECTION
    # ================================================================
    
    def _collect_project_data(self, project, revision) -> Dict[str, Any]:
        """جمع‌آوری داده‌های پروژه"""
        devices = revision.get_all_devices()
        
        # ===== I/O =====
        total_io = {
            'DI': sum(getattr(d, 'DI', 0) for d in devices),
            'DO': sum(getattr(d, 'DO', 0) for d in devices),
            'AI': sum(getattr(d, 'AI', 0) for d in devices),
            'AO': sum(getattr(d, 'AO', 0) for d in devices),
        }
        total_io['total'] = sum(total_io.values())
        
        # ===== کامپوننت‌ها =====
        component_usage = revision.get_component_usage()
        
        # ===== کنترلرها =====
        from math import ceil
        total = total_io['total']
        cbx = ceil(total / 64) if total > 0 else 0
        fbx = max(0, ceil(total / 16) - cbx) if total > 0 else 0
        
        # ===== آمار =====
        stats = {
            'total_sections': len(revision.sections),
            'total_devices': len(devices),
            'total_io': total,
            'cbx_count': cbx,
            'fbx_count': fbx,
        }
        
        # ===== تاریخ =====
        now = datetime.now()
        try:
            jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
            date_jalali = f"{jy}/{jm:02d}/{jd:02d}"
        except Exception:
            date_jalali = now.strftime('%Y/%m/%d')
        
        return {
            'project': project,
            'revision': revision,
            'devices': devices,
            'sections': revision.sections,
            'total_io': total_io,
            'component_usage': component_usage,
            'stats': stats,
            'date_jalali': date_jalali,
            'date_full': f"{date_jalali} {now.hour:02d}:{now.minute:02d}",
        }
    
    # ================================================================
    # BUILDERS
    # ================================================================
    
    def _build_title_page(self, project, revision, data) -> str:
        """صفحه عنوان"""
        return f"""╔══════════════════════════════════════════════════════════╗
║              {self.company_name}
║              {self.company_name_fa}
╚══════════════════════════════════════════════════════════╝

# سناریو کنترلی پیشنهادی BMS

**پروژه:** {project.name}
**رویژن:** {revision.name}
**مشتری:** {getattr(project, 'client_name', None) or '—'}
**مشاور:** {getattr(project, 'consultant_name', None) or '—'}
**پیمانکار:** {getattr(project, 'contractor_name', None) or self.company_name}
**طراح:** {getattr(project, 'designer_name', None) or self.designer_name}
**تاریخ:** {data['date_full']}
"""
    
    def _build_table_of_contents(self, sections_by_type: Dict) -> str:
        """فهرست مطالب"""
        lines = [
            "---",
            "## فهرست مطالب",
            "",
        ]
        
        counter = 1
        for section_type, sections in sections_by_type.items():
            if section_type == '_unknown':
                continue
            
            display_name = self.detector.get_section_type_display_name(section_type)
            lines.append(f"{counter}. سناریوی کنترلی {display_name}")
            counter += 1
        
        lines.extend([
            f"{counter}. لیست کامل نقاط کنترلی (I/O List)",
            f"{counter+1}. مشخصات کنترلرها",
            f"{counter+2}. لیست مواد (LOM)",
            "",
        ])
        
        return "\n".join(lines)
    
    def _build_intro(self, project, revision, data) -> str:
        """معرفی پروژه"""
        stats = data['stats']
        total_io = data['total_io']
        
        lines = [
            "---",
            "## ۱. معرفی پروژه",
            "",
            f"این سند فنی به منظور تشریح سناریوی کنترلی سیستم BMS "
            f"برای پروژه «{project.name}» تهیه شده است. "
            f"در این سند، معماری کنترل، منطق عملکرد تجهیزات، "
            f"نقاط کنترلی (I/O List) و لیست کامل مواد ارائه می‌گردد.",
            "",
            "### مشخصات کلی:",
            f"- **تعداد سکشن‌ها:** {stats['total_sections']}",
            f"- **تعداد دستگاه‌ها:** {stats['total_devices']}",
            f"- **مجموع I/O:** {stats['total_io']} نقطه",
            "",
            "### توزیع I/O:",
            f"- DI (ورودی دیجیتال): {total_io['DI']}",
            f"- DO (خروجی دیجیتال): {total_io['DO']}",
            f"- AI (ورودی آنالوگ): {total_io['AI']}",
            f"- AO (خروجی آنالوگ): {total_io['AO']}",
            "",
            "### کنترلرهای مورد نیاز:",
            f"- CBX-8R8: {stats['cbx_count']} دستگاه",
            f"- FBX-8R8: {stats['fbx_count']} دستگاه",
            "",
        ]
        
        return "\n".join(lines)
    
    def _build_architecture(self, data) -> str:
        """معماری سیستم"""
        lines = [
            "---",
            "## ۲. معماری سیستم کنترل",
            "",
            "سیستم کنترل BMS بر بستر سخت‌افزار ABB و Danfoss پیاده‌سازی می‌گردد. "
            "معماری سیستم به صورت توزیع‌شده (Distributed) بوده و تمام تجهیزات "
            "از طریق شبکه Modbus RTU/TCP یا سیم‌کشی مستقیم به کنترلرهای مرکزی "
            "متصل می‌شوند.",
            "",
            "### کامپوننت‌های پرکاربرد در این پروژه:",
            "",
        ]
        
        # ===== مرتب‌سازی کامپوننت‌ها =====
        comp_usage = data['component_usage']
        sorted_comps = sorted(comp_usage.items(), key=lambda x: x[1], reverse=True)
        
        for comp_key, count in sorted_comps[:15]:
            label_fa = COMPONENT_LABELS.get(comp_key, {}).get('fa', comp_key)
            label_en = COMPONENT_LABELS.get(comp_key, {}).get('en', comp_key)
            lines.append(f"- **{label_fa}** ({comp_key}): {count} عدد — {label_en}")
        
        lines.append("")
        lines.append("### بستر ارتباطی:")
        lines.append("- Modbus RTU (RS-485) برای تجهیزات نزدیک")
        lines.append("- Modbus TCP برای شبکه اصلی")
        lines.append("- BACnet (اختیاری) برای یکپارچه‌سازی با BMS های دیگر")
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_section_content(
        self,
        section_type: str,
        sections: List,
        data: Dict
    ) -> str:
        """محتوای یک سکشن تخصصی"""
        display_name = self.detector.get_section_type_display_name(section_type)
        
        # ===== تلاش برای قالب اختصاصی =====
        template = self._load_section_template(section_type)
        
        if not template:
            template = self._get_default_section_text(section_type)
        
        # ===== جایگزینی متغیرها =====
        template = self._replace_variables(template, data, section_type)
        
        lines = [
            "---",
            f"## سناریوی کنترلی {display_name}",
            "",
        ]
        
        # ===== تصویر (اگر موجود باشد) =====
        image_md = self._get_section_image_markdown(section_type)
        if image_md:
            lines.append(image_md)
            lines.append("")
        
        lines.append(template)
        lines.append("")
        
        # ===== لیست سکشن‌های این نوع =====
        lines.append(f"### سکشن‌های «{display_name}» در این پروژه:")
        lines.append("")
        
        for section in sections:
            devices_count = len(section.devices)
            section_io = section.get_total_io()
            lines.append(
                f"- **{section.name}** — "
                f"{devices_count} دستگاه، {section_io} I/O"
            )
        
        lines.append("")
        
        # ===== لیست دستگاه‌ها =====
        for section in sections:
            if not section.devices:
                continue
            
            lines.append(f"#### دستگاه‌های سکشن «{section.name}»:")
            lines.append("")
            lines.append("| # | نام دستگاه | توضیحات | DI | DO | AI | AO | مجموع |")
            lines.append("|---|------------|---------|----|----|----|----|-------|")
            
            for i, device in enumerate(section.devices, 1):
                name = getattr(device, 'Name', None) or f"Device_{i}"
                desc = (getattr(device, 'Description', None) or '—')[:40]
                di = getattr(device, 'DI', 0)
                do = getattr(device, 'DO', 0)
                ai = getattr(device, 'AI', 0)
                ao = getattr(device, 'AO', 0)
                total = di + do + ai + ao
                
                lines.append(
                    f"| {i} | {name} | {desc} | "
                    f"{di} | {do} | {ai} | {ao} | {total} |"
                )
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_section_io_list(self, sections: List, data: Dict) -> str:
        """لیست I/O فقط برای سکشن‌های داده شده"""
        devices = []
        for section in sections:
            devices.extend(section.devices)
        
        if not devices:
            return ""
        
        lines = [
            "---",
            "## لیست نقاط کنترلی این بخش",
            "",
            f"**تعداد دستگاه‌ها:** {len(devices)}",
            "",
            "| # | نام دستگاه | DI | DO | AI | AO | مجموع |",
            "|---|------------|----|----|----|----|-------|",
        ]
        
        total = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0, 'total': 0}
        
        for i, device in enumerate(devices, 1):
            di = getattr(device, 'DI', 0)
            do = getattr(device, 'DO', 0)
            ai = getattr(device, 'AI', 0)
            ao = getattr(device, 'AO', 0)
            t = di + do + ai + ao
            
            total['DI'] += di
            total['DO'] += do
            total['AI'] += ai
            total['AO'] += ao
            total['total'] += t
            
            name = getattr(device, 'Name', None) or f"Device_{i}"
            lines.append(
                f"| {i} | {name} | "
                f"{di} | {do} | {ai} | {ao} | {t} |"
            )
        
        lines.append(
            f"| | **TOTAL** | **{total['DI']}** | **{total['DO']}** | "
            f"**{total['AI']}** | **{total['AO']}** | **{total['total']}** |"
        )
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_io_list(self, data) -> str:
        """لیست کامل I/O"""
        devices = data['devices']
        
        lines = [
            "---",
            "## لیست کامل نقاط کنترلی (I/O List)",
            "",
            f"مجموع **{len(devices)}** دستگاه با "
            f"**{data['total_io']['total']}** نقطه I/O.",
            "",
            "| # | نام دستگاه | سکشن | DI | DO | AI | AO | مجموع |",
            "|---|------------|------|----|----|----|----|-------|",
        ]
        
        # ===== پیدا کردن سکشن هر دستگاه =====
        device_sections = {}
        for section in data['sections']:
            for device in section.devices:
                device_sections[id(device)] = section.name
        
        for i, device in enumerate(devices, 1):
            name = getattr(device, 'Name', None) or f"Device_{i}"
            section_name = device_sections.get(id(device), '—')
            di = getattr(device, 'DI', 0)
            do = getattr(device, 'DO', 0)
            ai = getattr(device, 'AI', 0)
            ao = getattr(device, 'AO', 0)
            total = di + do + ai + ao
            
            lines.append(
                f"| {i} | {name} | {section_name} | "
                f"{di} | {do} | {ai} | {ao} | {total} |"
            )
        
        # ===== TOTAL =====
        lines.extend([
            "",
            f"| **TOTAL** | | | "
            f"**{data['total_io']['DI']}** | "
            f"**{data['total_io']['DO']}** | "
            f"**{data['total_io']['AI']}** | "
            f"**{data['total_io']['AO']}** | "
            f"**{data['total_io']['total']}** |",
            "",
        ])
        
        return "\n".join(lines)
    
    def _build_controller_requirements(self, data) -> str:
        """مشخصات کنترلرها"""
        stats = data['stats']
        total_io = data['total_io']['total']
        
        lines = [
            "---",
            "## مشخصات کنترلرها",
            "",
            f"برای پوشش **{total_io}** نقطه I/O نیاز به کنترلرهای زیر می‌باشد:",
            "",
            "| نوع کنترلر | تعداد | ظرفیت واحد | مجموع ظرفیت |",
            "|------------|-------|-----------|-------------|",
            f"| CBX-8R8 | **{stats['cbx_count']}** | 64 I/O | {stats['cbx_count'] * 64} I/O |",
        ]
        
        if stats['fbx_count'] > 0:
            lines.append(
                f"| FBX-8R8 | **{stats['fbx_count']}** | 16 I/O | "
                f"{stats['fbx_count'] * 16} I/O |"
            )
        
        total_capacity = stats['cbx_count'] * 64 + stats['fbx_count'] * 16
        spare = total_capacity - total_io
        
        lines.extend([
            "",
            "### توضیحات:",
            "- **CBX-8R8**: کنترلر اصلی با 64 I/O قابل توسعه",
            "- **FBX-8R8**: ماژول توسعه با 16 I/O",
            "- حداکثر ۳ ماژول FBX برای هر CBX",
            f"- **ظرفیت کل:** {total_capacity} I/O",
            f"- **I/O استفاده شده:** {total_io}",
            f"- **I/O ذخیره (Spare):** {spare}",
            "",
        ])
        
        return "\n".join(lines)
    
    def _build_lom(self, data) -> str:
        """لیست مواد (LOM)"""
        lines = [
            "---",
            "## لیست مواد (LOM)",
            "",
            "| # | کامپوننت | کد | تعداد |",
            "|---|----------|-----|-------|",
        ]
        
        comp_usage = data['component_usage']
        sorted_comps = sorted(comp_usage.items(), key=lambda x: x[1], reverse=True)
        
        total = 0
        for i, (comp_key, count) in enumerate(sorted_comps, 1):
            label_fa = COMPONENT_LABELS.get(comp_key, {}).get('fa', comp_key)
            lines.append(f"| {i} | {label_fa} | {comp_key} | {count} |")
            total += count
        
        lines.extend([
            "",
            f"| | | **TOTAL** | **{total}** |",
            "",
        ])
        
        return "\n".join(lines)
    
    def _build_footer(self, project, revision) -> str:
        """پایان سند"""
        return f"""---

═══════════════════════════════════════════════════════════════
پایان سند — {self.company_name}
پروژه: {project.name} | رویژن: {revision.name}
═══════════════════════════════════════════════════════════════"""
    
    # ================================================================
    # TEMPLATE MANAGEMENT (✅ اصلاح‌شده)
    # ================================================================
    
    def _load_section_template(self, section_type: str) -> Optional[str]:
        """
        بارگذاری قالب اختصاصی سکشن
        
        اولویت:
        1. دیتابیس (اگر importer موجود باشد)
        2. فایل .txt در proposal_templates/
        3. None (استفاده از متن پیش‌فرض)
        """
        # ===== ۱. دیتابیس =====
        if self.importer is not None:
            try:
                best_from_db = self.importer.get_best_template(section_type)
                if best_from_db:
                    logger.debug(f"✅ Loaded template from DB: {section_type}")
                    return best_from_db
            except Exception as e:
                logger.debug(f"Could not load from DB: {e}")
        
        # ===== ۲. فایل =====
        try:
            template_path = self.templates_dir / f"{section_type}.txt"
            if template_path.exists():
                logger.debug(f"✅ Loaded template from file: {section_type}")
                return template_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.debug(f"Could not load from file: {e}")
        
        return None
    
    def _replace_variables(
        self,
        template: str,
        data: Dict,
        section_type: str
    ) -> str:
        """جایگزینی متغیرها در قالب"""
        project = data['project']
        
        replacements = {
            '{{PROJECT_NAME}}': project.name,
            '{{COMPANY_NAME}}': self.company_name,
            '{{COMPANY_NAME_FA}}': self.company_name_fa,
            '{{CLIENT_NAME}}': getattr(project, 'client_name', None) or '—',
            '{{CONSULTANT_NAME}}': getattr(project, 'consultant_name', None) or '—',
            '{{CONTRACTOR_NAME}}': getattr(project, 'contractor_name', None) or self.company_name,
            '{{DESIGNER_NAME}}': getattr(project, 'designer_name', None) or self.designer_name,
            '{{REVISION}}': data['revision'].name,
            '{{DATE}}': data['date_jalali'],
            '{{SECTION_TYPE}}': section_type,
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, str(value))
        
        return result
    
    def _get_section_image_markdown(self, section_type: str) -> Optional[str]:
        """
        ✅ جدید: برگرداندن Markdown تصویر اگر فایل موجود باشد
        """
        image_name = self.section_images.get(section_type)
        if not image_name:
            return None
        
        try:
            image_path = self.images_dir / image_name
            if image_path.exists():
                # مسیر نسبی برای Word Exporter
                return f"![{section_type}]({image_path})"
        except Exception:
            pass
        
        return None
    
    # ================================================================
    # DEFAULT SECTION TEXT
    # ================================================================
    
    def _get_default_section_text(self, section_type: str) -> str:
        """متن پیش‌فرض برای سکشن‌هایی که قالب ندارند"""
        defaults = {
            'boiler': """### کلیات و معماری سیستم
بویلرها به صورت پیش‌فرض دارای کنترلر محلی (LOCAL PANEL) جهت مدیریت عملکرد مشعل، کنترل سوخت و پایش پارامترهای ایمنی داخلی خود هستند. به منظور یکپارچه‌سازی با سیستم BMS، نظارت مداوم و بهینه‌سازی مصرف انرژی، سنسورهای دمای مستغرق (IMMERSION TEMPERATURE SENSORS) بر روی کلکتورها و مسیرهای رفت و برگشت آب نصب می‌گردند.

### منطق راه‌اندازی و توقف
**راه‌اندازی (START-UP):** پیش از راه‌اندازی هر دیگ، سیستم BMS ابتدا فرمان راه‌اندازی پمپ سیرکولاسیون مربوطه را صادر می‌کند. پس از دریافت سیگنال کارکرد پمپ و تأیید جریان آب توسط فلوسوئیچ، فرمان «اجازه کار» به تابلوی بویلر ارسال می‌شود.

**توقف (SHUTDOWN):** در زمان خروج دیگ از مدار، ابتدا فرمان خاموش شدن بویلر از سوی BMS صادر می‌شود. جهت جلوگیری از تنش حرارتی، پمپ مربوطه پس از یک تأخیر زمانی مشخص (PUMP OVERRUN) خاموش خواهد شد.

### مدیریت ظرفیت (STAGING)
BMS با توجه به تغییرات بار حرارتی در ساعات مختلف، تعداد دیگ‌های در حال کار را به صورت هوشمند مدیریت می‌کند.""",
            
            'chiller': """### کلیات و معماری سیستم
چیلرهای هوا خنک به صورت پکیج مستقل در فضای آزاد نصب می‌شوند و هر دستگاه مجهز به یک کنترلر محلی (LOCAL PANEL) جهت مدیریت دقیق کمپرسورها، فن‌های کندانسور، شیر انبساط الکترونیکی (EEV) و حفاظت‌های سیکل تبرید است.

### منطق راه‌اندازی و توقف
**راه‌اندازی (START-UP):** برای جلوگیری از یخ‌زدگی اواپراتور، سیستم BMS پیش از صدور هرگونه فرمان به چیلر ابتدا پمپ آب سرد (CHWP) مربوطه را روشن می‌کند. پس از دریافت سیگنال کارکرد پمپ و تأیید برقراری جریان آب توسط فلوسوئیچ، فرمان «اجازه کار» به تابلوی چیلر ارسال می‌گردد.

**توقف (SHUTDOWN):** در زمان کاهش بار برودتی، ابتدا فرمان ENABLE از سوی BMS قطع می‌شود. جهت تخلیه کامل برودت، پمپ آب سرد باید ۳ تا ۵ دقیقه پس از خاموشی کامل چیلر به کار خود ادامه دهد (PUMP OVERRUN).

### مدیریت ظرفیت و جایگزینی
- **مدیریت ظرفیت (STAGING):** ورود و خروج چیلرها بر اساس دمای رفت و برگشت هدر اصلی
- **چرخش نوبت کارکرد (WEAR LEVELING):** یکسان‌سازی ساعات کارکرد
- **جایگزینی خودکار (AUTO-CHANGEOVER):** در صورت بروز خطا""",
            
            'ahu': """### کلیات و معماری سیستم
هواسازها (AHU) به عنوان یکی از اصلی‌ترین تجهیزات HVAC ساختمان، وظیفه تأمین هوای تازه، فیلتراسیون، گرمایش/سرمایش و توزیع هوا در فضاهای مختلف را بر عهده دارند.

### منطق کنترلی
- کنترل دمای هوای رفت و برگشت
- کنترل رطوبت (در صورت وجود humidifier)
- کنترل دمپر هوای تازه و برگشت
- کنترل فن‌های SUPPLY و RETURN
- فیلتراسیون و پایش افت فشار فیلترها""",
            
            'fancoil': """### کلیات
فن‌کویل‌ها به عنوان تجهیزات نهایی توزیع حرارت/برودت در فضاهای ساختمان، شامل یک کویل آب گرم/سرد و یک فن می‌باشند.

### منطق کنترلی
- کنترل دمای اتاق از طریق ترموستات
- کنترل سرعت فن (Low/Medium/High)
- کنترل شیر آب گرم/سرد""",
            
            'dhw': """### کلیات و فلسفه عملکرد
تأمین آبگرم بهداشتی ساختمان به عهده منابع کویلی است. مکانیزم حرارتی به این صورت است که آبگرم تولید شده در مدار اولیه (دیگ‌ها) به داخل کویل‌های مسی مخزن هدایت شده و از طریق تبادل حرارتی با سیال پیرامون کویل، دمای آب مصرفی را افزایش می‌دهد.

### منطق کنترل دما (TEMPERATURE CONTROL LOGIC)
با استفاده از سنسور مستغرق (IMMERSION SENSOR) نصب شده روی مخزن، سیستم BMS دمای آب مصرفی را به صورت لحظه‌ای پایش می‌کند. بر اساس نقطه تنظیم (SETPOINT) تعریف شده توسط اپراتور، سیستم یک فرمان تدریجی (آنالوگ) به اکچویتور شیر کنترل (MODULATING VALVE) تعبیه شده در مسیر ورود آب گرم به کویل ارسال می‌کند.

### مدیریت پمپ‌های سیرکولاسیون
- **DUTY/STANDBY**: دو پمپ به صورت یکپارچه کار
- **WEAR LEVELING**: یکسان‌سازی استهلاک
- **AUTO-CHANGEOVER**: جایگزینی خودکار""",
            
            'expansion_tank': """### کلیات
منابع انبساط بسته وظیفه جبران تغییرات حجم آب در سیستم‌های بسته را بر عهده دارند. سیستم BMS با پایش فشار و سطح، وضعیت سلامت منبع را کنترل می‌کند.

### تجهیزات ابزار دقیق
- **PRESSURE TRANSMITTER**: اندازه‌گیری فشار گاز درون مخزن
- **LEVEL TRANSMITTER/SWITCH**: اندازه‌گیری حجم آب
- **GAS INLET SOLENOID VALVE**: تزریق گاز
- **GAS VENT SOLENOID VALVE**: تخلیه گاز
- **WATER MAKE-UP SOLENOID VALVE**: جبران آب

### منطق کنترل فشار (GAS PRESSURE CONTROL)
سیستم BMS به صورت پیوسته اطلاعات سنسور فشار را تحلیل می‌کند. فشار گاز باید ۲ PSI بالاتر از فشار استاتیک پمپ‌های شبکه نگه داشته شود.""",
            
            'booster_pump': """### کلیات و مرزبندی کنترلی
با توجه به الزامات ایمنی و استانداردهای حریق، کنترل بوسترپمپ‌های آبرسانی و آتش‌نشانی به صورت کاملاً مستقل و خودکار توسط تابلو برق و کنترلر اختصاصی همان پکیج انجام می‌پذیرد.

سیستم BMS در این بخش هیچ‌گونه فرمان مستقیمی صادر نمی‌کند و نقش آن منحصراً به مانیتورینگ نظارتی، ثبت داده‌ها و مدیریت آلارم‌ها محدود می‌گردد.

### نقاط تحت پایش
- وضعیت خطای عمومی تابلو
- وضعیت خطای پمپ‌ها (به تفکیک)
- فشار کلکتور خروجی
- وضعیت کارکرد پمپ‌ها""",
            
            'primary_loop': """### کلیات
در طراحی سیستم‌های مدرن موتورخانه، اغلب از دو مدار مستقل استفاده می‌شود: مدار اولیه (PRIMARY LOOP) و مدار ثانویه (SECONDARY LOOP).

### مشخصات مدار اولیه
- مستقیماً شامل منبع تولید حرارت یا سرما (دیگ یا چیلر) است
- جریان معمولاً ثابت است
- توسط پمپ مدار اولیه کنترل می‌شود
- هدف: حفظ جریان ثابت از طریق دیگ/چیلر برای جلوگیری از نوسانات دما و فشار

### منطق کنترلی
سیستم BMS کلیه وضعیت‌های پمپ‌ها را در تابلو قدرت پایش می‌کند:
- حالت کلید (دستی/اتوماتیک/خاموش)
- وضعیت کنتاکتور و بیمتال
- فرمان به کنتاکتور""",
            
            'secondary_loop': """### کلیات
برای کنترل پمپ‌های دور متغیر مدار ثانویه، از سیستم کنترلر پمپ بر اساس اختلاف فشار ثابت استفاده می‌شود (CONSTANT DIFFERENTIAL PRESSURE PUMP CONTROLLER).

### منطق کنترلی
سنسورهای فشار بر روی کلکتورهای پمپ‌های مدار ثانویه و همچنین مسیر برگشت نصب می‌شوند. برای پمپ‌هایی که دو یا بیشتر خط برگشت دارند، بر روی همه خطوط برگشت سنسور فشار نصب می‌شود.

### محاسبه شیرهای پای‌پاس (PRC)
اختلاف فشار مورد نیاز برای نقطه کارکرد پمپ، با یک بار اندازه‌گیری در هنگام راه‌اندازی به دست می‌آید.""",
            
            'hardware': """### کلیات
سیستم کنترل BMS بر بستر سخت‌افزار ABB و Danfoss پیاده‌سازی می‌گردد.

### کنترلرها
- **CBX-8R8**: کنترلر اصلی با 64 I/O قابل توسعه
- **FBX-8R8**: ماژول توسعه با 16 I/O
- **MCX-08m2**: کنترلر مستقل 8DI/8DO/8AI/4AO
- **MCX-06D**: کنترلر مستقل 8DI/6DO/4AI/2AO

### بستر ارتباطی
- Modbus RTU/TCP
- BACnet (اختیاری)""",
            
            'panel': """### کلیات
تابلوی کنترل BMS شامل موارد زیر می‌باشد:

### اجزای تابلو
- PLC اصلی (CBX-8R8)
- ماژول‌های I/O (FBX-8R8)
- منابع تغذیه 24VDC
- ترمینال‌های ورودی/خروجی
- رله‌های کمکی
- کلیدهای انتخاب (Selector)
- چراغ‌های نشانگر
- HMI (در صورت نیاز)

### استانداردها
- IP54 (حداقل)
- مطابق IEC 61439""",
        }
        
        return defaults.get(
            section_type,
            f"### سناریوی کنترلی {section_type}\n\n"
            f"توضیحات تخصصی برای این بخش در حال تهیه می‌باشد.\n\n"
            f"سیستم BMS کلیه نقاط کنترلی این تجهیزات را پایش و کنترل می‌کند."
        )


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['LocalProposalGenerator']