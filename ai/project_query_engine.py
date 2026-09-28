# ai/project_query_engine.py
"""
Project Query Engine — استخراج داده از دیتابیس برای پاسخ به سوالات کاربر

این ماژول:
1. سوال کاربر را با Regex پارس می‌کند
2. داده‌ی مرتبط را از دیتابیس استخراج می‌کند
3. Context آماده برای AI می‌سازد
"""

import logging
from typing import Dict, List, Optional, Any , Tuple   
from collections import defaultdict

from ai.query_templates import (
    detect_intent,
    normalize_component,
    COMPONENT_ALIASES,
)
from ai.project_matcher import ProjectMatcher

logger = logging.getLogger(__name__)


class ProjectQueryEngine:
    """
    موتور Query برای پاسخ به سوالات کاربر درباره‌ی پروژه
    """
    
    def __init__(self, db_manager, app):
        """
        Args:
            db_manager: DatabaseManager
            app: MotorApp
        """
        self.db = db_manager
        self.app = app
        self.matcher = ProjectMatcher(db_manager, app)
    
    # ================================================================
    # MAIN ENTRY POINT
    # ================================================================
    def _resolve_project_name(self, raw_name: str) -> Tuple[Optional[str], float, str]:
        """
        تبدیل نام خام به نام واقعی پروژه
        
        Returns:
            (project_name, confidence, method)
        """
        if not raw_name:
            return (None, 0.0, 'none')
        
        project_names = list(self.app.projects.keys())
        return self.matcher.match(raw_name, project_names)
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        پردازش سوال و ساخت Context
        
        Returns:
            {
                'intent': str,
                'data': dict,           # داده استخراج‌شده
                'context': str,         # متن Context برای AI
                'can_answer_directly': bool,  # آیا نیازی به AI نیست؟
                'direct_answer': str,   # پاسخ مستقیم (اگر بشه)
            }
        """
        try:
            # ===== 1. تشخیص intent =====
            project_names = list(self.app.projects.keys())
            parsed = detect_intent(question, project_names)
            intent = parsed['intent']
            
            logger.info(f"🔍 Detected intent: {intent} for question: {question}")
            
            # ===== 2. پاسخ بر اساس intent =====
            if intent == 'count_components':
                return self._handle_count_components(parsed)
            
            elif intent == 'list_sections':
                return self._handle_list_sections(parsed)
            
            elif intent == 'list_devices':
                return self._handle_list_devices(parsed)
            
            elif intent == 'project_summary':
                return self._handle_project_summary(parsed)
            
            elif intent == 'compare_projects':
                return self._handle_compare_projects(parsed)
            
            elif intent == 'top_components':
                return self._handle_top_components(parsed)
            
            elif intent == 'list_projects':
                return self._handle_list_projects(parsed)

            elif intent == 'count_projects':
                return self._handle_count_projects(parsed)
            
            elif intent == 'total_io':
                return self._handle_total_io(parsed)
            
            elif intent == 'search_devices':
                return self._handle_search_devices(parsed)
            
            else:
                # ===== fallback: ارسال به AI با Context کلی =====
                return self._handle_general_question(question)
        
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return {
                'intent': 'error',
                'data': {},
                'context': f"خطا در پردازش: {e}",
                'can_answer_directly': True,
                'direct_answer': f"❌ خطا در پردازش سوال: {e}",
            }
    
    # ================================================================
    # HANDLERS
    # ================================================================
    
    def _handle_count_components(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «چند X در پروژه Y دارم؟»"""
        groups = parsed['groups']
        
        # ===== استخراج کامپوننت =====
        component_name = groups[0] if groups else None
        component_key = normalize_component(component_name) if component_name else None
        
        # ===== استخراج پروژه =====
        project_name_raw = None
        if len(groups) >= 2:
            project_name_raw = groups[1].strip().strip('"\'').strip()
        
        # ===== ✅ تطبیق هوشمند پروژه =====
        project_name = None
        if project_name_raw:
            matched_name, confidence, method = self._resolve_project_name(project_name_raw)
            
            if matched_name:
                project_name = matched_name
                logger.info(
                    f"✅ Matched '{project_name_raw}' → '{project_name}' "
                    f"(via {method}, {confidence:.0%})"
                )
            else:
                project_name = project_name_raw
                logger.warning(f"⚠️ No match for '{project_name_raw}' — using raw name")
        
        # ===== اگر پروژه مشخص نشد، از پروژه فعلی استفاده کن =====
        if not project_name:
            project = self.app.get_current_project()
            if not project:
                return self._no_project_response()
            project_name = project.name
        
        # ===== چک وجود پروژه =====
        project = self.app.projects.get(project_name)
        if not project:
            return {
                'intent': 'count_components',
                'data': {},
                'context': f"پروژه '{project_name}' یافت نشد.",
                'can_answer_directly': True,
                'direct_answer': f"❌ پروژه‌ای با نام '{project_name}' پیدا نشد.",
            }
        
        # ===== اگر کامپوننت مشخص نشد =====
        if not component_key:
            return {
                'intent': 'count_components',
                'data': {'project_name': project_name},
                'context': f"کاربر دنبال کامپوننت '{component_name}' است اما این کامپوننت شناسایی نشد.",
                'can_answer_directly': True,
                'direct_answer': (
                    f"❌ کامپوننت '{component_name}' شناسایی نشد.\n\n"
                    f"لطفاً از کد کامپوننت استفاده کنید (مثل PU, PT, DTS, ITS)."
                ),
            }
        
        # ===== شمارش در همه Revision ها =====
        total_count = 0
        revision_breakdown = {}
        
        for revision in project.revisions:
            rev_count = 0
            for device in revision.get_all_devices():
                qty = getattr(device, component_key, 0)
                rev_count += int(qty or 0)
            
            revision_breakdown[revision.name] = rev_count
            total_count += rev_count
        
        # ===== ساخت پاسخ مستقیم =====
        component_label = self._get_component_label(component_key, 'fa')
        component_label_en = self._get_component_label(component_key, 'en')
        
        direct_answer = f"""
    📊 **تعداد {component_label} ({component_key})**

    **پروژه:** {project_name}
    **کامپوننت:** {component_label_en}
    **تعداد کل:** **{total_count}**

    """
        if len(revision_breakdown) > 1:
            direct_answer += "**تفکیک بر اساس Revision:**\n"
            for rev_name, count in revision_breakdown.items():
                marker = "📌" if rev_name == project.current_revision_name else "📎"
                direct_answer += f"  {marker} {rev_name}: {count}\n"
        else:
            rev_name = list(revision_breakdown.keys())[0]
            direct_answer += f"**Revision:** {rev_name}\n"
        
        return {
            'intent': 'count_components',
            'data': {
                'project_name': project_name,
                'component': component_key,
                'total': total_count,
                'by_revision': revision_breakdown,
            },
            'context': direct_answer,
            'can_answer_directly': True,
            'direct_answer': direct_answer,
        }
    
    def _handle_list_sections(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «سکشن‌های پروژه X چیه؟»"""
        groups = parsed['groups']
        project_name_raw = groups[0].strip().strip('"\'').strip() if groups else None
        
        # ===== ✅ تطبیق هوشمند =====
        project_name = None
        if project_name_raw:
            matched_name, confidence, method = self._resolve_project_name(project_name_raw)
            
            if matched_name:
                project_name = matched_name
                logger.info(
                    f"✅ Matched '{project_name_raw}' → '{project_name}' "
                    f"(via {method}, {confidence:.0%})"
                )
            else:
                project_name = project_name_raw
        
        # ===== پروژه فعلی =====
        if not project_name:
            project = self.app.get_current_project()
            if not project:
                return self._no_project_response()
            project_name = project.name
        
        project = self.app.projects.get(project_name)
        if not project:
            return self._project_not_found(project_name)
        
        # ===== لیست سکشن‌ها =====
        current_rev = project.get_current_revision()
        if not current_rev:
            return self._no_revision_response(project_name)
        
        sections = current_rev.sections
        
        # ===== ساخت پاسخ =====
        answer = f"📋 **سکشن‌های پروژه {project_name}**\n\n"
        answer += f"**Revision:** {current_rev.name}\n"
        answer += f"**تعداد سکشن:** {len(sections)}\n\n"
        
        for i, section in enumerate(sections, 1):
            device_count = len(section.devices)
            section_io = section.get_total_io()
            answer += f"**{i}. {section.name}**\n"
            answer += f"   • تعداد دستگاه: {device_count}\n"
            answer += f"   • مجموع I/O: {section_io}\n"
            if section.description:
                answer += f"   • توضیحات: {section.description}\n"
            answer += "\n"
        
        return {
            'intent': 'list_sections',
            'data': {
                'project_name': project_name,
                'revision': current_rev.name,
                'sections': [s.name for s in sections],
            },
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }
    
    def _handle_list_devices(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «دستگاه‌های سکشن X چیه؟»"""
        groups = parsed['groups']
        section_name = groups[0].strip().strip('"\'').strip() if groups else None
        
        if not section_name:
            return self._general_error("نام سکشن مشخص نشد")
        
        # ===== جستجو در همه پروژه‌ها =====
        found_sections = []
        for proj_name, project in self.app.projects.items():
            for revision in project.revisions:
                section = revision.get_section_by_name(section_name)
                if section:
                    found_sections.append({
                        'project': proj_name,
                        'revision': revision.name,
                        'section': section,
                    })
        
        if not found_sections:
            return {
                'intent': 'list_devices',
                'data': {},
                'context': f"سکشن '{section_name}' یافت نشد.",
                'can_answer_directly': True,
                'direct_answer': f"❌ سکشنی با نام '{section_name}' پیدا نشد.",
            }
        
        # ===== ساخت پاسخ =====
        answer = f"📋 **دستگاه‌های سکشن {section_name}**\n\n"
        
        for item in found_sections[:5]:  # حداکثر 5 مورد
            section = item['section']
            answer += f"**پروژه:** {item['project']}  |  **Revision:** {item['revision']}\n"
            answer += f"**تعداد دستگاه:** {len(section.devices)}\n\n"
            
            for i, device in enumerate(section.devices, 1):
                name = device.Name or f"Device_{i}"
                desc = device.Description or "—"
                total_io = device.get_total_io()
                answer += f"  {i}. **{name}** — {desc}\n"
                answer += f"     I/O: DI={device.DI}, DO={device.DO}, AI={device.AI}, AO={device.AO}, Total={total_io}\n"
            answer += "\n"
        
        return {
            'intent': 'list_devices',
            'data': {'found_sections': len(found_sections)},
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }
    
    def _handle_project_summary(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «خلاصه پروژه X»"""
        groups = parsed['groups']
        project_name_raw = groups[0].strip().strip('"\'').strip() if groups else None
        
        # ===== ✅ تطبیق هوشمند =====
        project_name = None
        if project_name_raw:
            matched_name, confidence, method = self._resolve_project_name(project_name_raw)
            
            if matched_name:
                project_name = matched_name
                logger.info(
                    f"✅ Matched '{project_name_raw}' → '{project_name}' "
                    f"(via {method}, {confidence:.0%})"
                )
            else:
                # اگر تطبیق پیدا نشد، از نام خام استفاده کن
                project_name = project_name_raw
                logger.warning(f"⚠️ No match for '{project_name_raw}' — using raw name")
        
        # ===== اگر پروژه مشخص نشد → پروژه فعلی =====
        if not project_name:
            project = self.app.get_current_project()
            if not project:
                return self._no_project_response()
            project_name = project.name
        
        # ===== چک وجود پروژه =====
        project = self.app.projects.get(project_name)
        if not project:
            return self._project_not_found(project_name)
        
        # ===== ساخت خلاصه =====
        current_rev = project.get_current_revision()
        if not current_rev:
            return self._no_revision_response(project_name)
        
        stats = current_rev.get_statistics()
        
        # ===== کامپوننت‌های پرکاربرد =====
        component_usage = current_rev.get_component_usage()
        top_components = sorted(
            component_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # ===== ساخت پاسخ =====
        answer = f"📊 **خلاصه پروژه: {project.name}**\n\n"
        answer += f"**Revision فعلی:** {current_rev.name}\n"
        answer += f"**تعداد Revision ها:** {len(project.revisions)}\n\n"
        
        answer += "**📁 ساختار:**\n"
        answer += f"  • تعداد سکشن: {stats['total_sections']}\n"
        answer += f"  • تعداد دستگاه: {stats['total_devices']}\n"
        answer += f"  • دستگاه‌های فعال: {stats['active_devices']}\n\n"
        
        answer += "**📈 I/O:**\n"
        answer += f"  • DI: {stats['total_di']}\n"
        answer += f"  • DO: {stats['total_do']}\n"
        answer += f"  • AI: {stats['total_ai']}\n"
        answer += f"  • AO: {stats['total_ao']}\n"
        answer += f"  • **مجموع: {stats['total_io']}**\n\n"
        
        if top_components:
            answer += "**🔧 کامپوننت‌های پرکاربرد:**\n"
            for comp_key, count in top_components:
                label = self._get_component_label(comp_key, 'fa')
                answer += f"  • {label} ({comp_key}): {count}\n"
        
        return {
            'intent': 'project_summary',
            'data': {'project_name': project_name, 'stats': stats},
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }
    
    def _handle_compare_projects(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «مقایسه پروژه X و Y»"""
        groups = parsed['groups']
        if len(groups) < 2:
            return self._general_error("نام دو پروژه مشخص نشد")
        
        proj_a_raw = groups[0].strip().strip('"\'').strip()
        proj_b_raw = groups[1].strip().strip('"\'').strip()
        
        # ===== ✅ تطبیق هوشمند هر دو پروژه =====
        proj_a_name, conf_a, method_a = self._resolve_project_name(proj_a_raw)
        proj_b_name, conf_b, method_b = self._resolve_project_name(proj_b_raw)
        
        if proj_a_name:
            logger.info(f"✅ Matched '{proj_a_raw}' → '{proj_a_name}' ({method_a}, {conf_a:.0%})")
        if proj_b_name:
            logger.info(f"✅ Matched '{proj_b_raw}' → '{proj_b_name}' ({method_b}, {conf_b:.0%})")
        
        # ===== اگر یکی از پروژه‌ها پیدا نشد =====
        if not proj_a_name or not proj_b_name:
            missing = []
            if not proj_a_name:
                missing.append(proj_a_raw)
            if not proj_b_name:
                missing.append(proj_b_raw)
            
            return {
                'intent': 'compare_projects',
                'data': {},
                'context': f"پروژه‌های یافت‌نشده: {', '.join(missing)}",
                'can_answer_directly': True,
                'direct_answer': (
                    f"❌ پروژه‌ی «{', '.join(missing)}» پیدا نشد.\n\n"
                    f"**لیست پروژه‌های موجود:**\n" +
                    "\n".join(f"  • {n}" for n in self.app.projects.keys())
                ),
            }
        
        proj_a = self.app.projects.get(proj_a_name)
        proj_b = self.app.projects.get(proj_b_name)
        
        rev_a = proj_a.get_current_revision()
        rev_b = proj_b.get_current_revision()
        
        stats_a = rev_a.get_statistics() if rev_a else {}
        stats_b = rev_b.get_statistics() if rev_b else {}
        
        # ===== ساخت جدول مقایسه =====
        answer = f"⚖️ **مقایسه دو پروژه**\n\n"
        answer += f"| ویژگی | {proj_a.name} | {proj_b.name} |\n"
        answer += f"|-------|----------|----------|\n"
        answer += f"| سکشن‌ها | {stats_a.get('total_sections', 0)} | {stats_b.get('total_sections', 0)} |\n"
        answer += f"| دستگاه‌ها | {stats_a.get('total_devices', 0)} | {stats_b.get('total_devices', 0)} |\n"
        answer += f"| DI | {stats_a.get('total_di', 0)} | {stats_b.get('total_di', 0)} |\n"
        answer += f"| DO | {stats_a.get('total_do', 0)} | {stats_b.get('total_do', 0)} |\n"
        answer += f"| AI | {stats_a.get('total_ai', 0)} | {stats_b.get('total_ai', 0)} |\n"
        answer += f"| AO | {stats_a.get('total_ao', 0)} | {stats_b.get('total_ao', 0)} |\n"
        answer += f"| **مجموع I/O** | **{stats_a.get('total_io', 0)}** | **{stats_b.get('total_io', 0)}** |\n"
        
        return {
            'intent': 'compare_projects',
            'data': {'proj_a': stats_a, 'proj_b': stats_b},
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }
    
    def _handle_top_components(self, parsed: Dict) -> Dict[str, Any]:
        """
        پاسخ به «پرکاربردترین کامپوننت در پروژه X»
        
        ✅ جدید: پیاده‌سازی کامل (نه فقط project_summary)
        """
        groups = parsed['groups']
        project_name_raw = groups[0].strip().strip('"\'').strip() if groups else None
        
        # ===== تطبیق هوشمند پروژه =====
        project_name = None
        if project_name_raw:
            matched_name, confidence, method = self._resolve_project_name(project_name_raw)
            
            if matched_name:
                project_name = matched_name
                logger.info(
                    f"✅ Matched '{project_name_raw}' → '{project_name}' "
                    f"(via {method}, {confidence:.0%})"
                )
            else:
                project_name = project_name_raw
        
        # ===== پروژه فعلی =====
        if not project_name:
            project = self.app.get_current_project()
            if not project:
                return self._no_project_response()
            project_name = project.name
        
        project = self.app.projects.get(project_name)
        if not project:
            return self._project_not_found(project_name)
        
        current_rev = project.get_current_revision()
        if not current_rev:
            return self._no_revision_response(project_name)
        
        # ============================================================
        # ✅ محاسبه Top Components
        # ============================================================
        component_usage = current_rev.get_component_usage()
        
        if not component_usage:
            return {
                'intent': 'top_components',
                'data': {'project_name': project_name},
                'context': f"پروژه '{project_name}' هیچ کامپوننتی ندارد.",
                'can_answer_directly': True,
                'direct_answer': f"📊 پروژه **{project_name}** هیچ کامپوننتی ندارد.",
            }
        
        # ===== مرتب‌سازی =====
        sorted_components = sorted(
            component_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # ===== محاسبه کل =====
        total_components = sum(component_usage.values())
        
        # ============================================================
        # ✅ ساخت پاسخ
        # ============================================================
        answer = f"🔝 **پرکاربردترین کامپوننت‌ها در پروژه {project.name}**\n\n"
        answer += f"**Revision:** {current_rev.name}\n"
        answer += f"**مجموع کامپوننت‌ها:** {total_components}\n"
        answer += f"**تعداد انواع:** {len(component_usage)}\n\n"
        
        answer += "**🏆 ۱۰ کامپوننت اول:**\n"
        
        for i, (comp_key, count) in enumerate(sorted_components[:10], 1):
            label_fa = self._get_component_label(comp_key, 'fa')
            label_en = self._get_component_label(comp_key, 'en')
            
            # ===== درصد =====
            percent = (count / total_components * 100) if total_components > 0 else 0
            
            # ===== نشان =====
            if i == 1:
                icon = "🥇"
            elif i == 2:
                icon = "🥈"
            elif i == 3:
                icon = "🥉"
            else:
                icon = f"{i}."
            
            answer += (
                f"{icon} **{label_fa}** ({comp_key}) — "
                f"**{count}** عدد ({percent:.1f}%)\n"
            )
        
        if len(sorted_components) > 10:
            answer += f"\n... و {len(sorted_components) - 10} کامپوننت دیگر\n"
        
        return {
            'intent': 'top_components',
            'data': {
                'project_name': project_name,
                'top_components': sorted_components[:10],
                'total': total_components,
            },
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }
    
    def _handle_list_projects(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «چه پروژه‌هایی دارم؟»"""
        projects = self.app.projects
        
        answer = f"📁 **پروژه‌های موجود ({len(projects)} پروژه)**\n\n"
        
        for i, (name, project) in enumerate(projects.items(), 1):
            current_rev = project.get_current_revision()
            sections = len(current_rev.sections) if current_rev else 0
            devices = len(current_rev.get_all_devices()) if current_rev else 0
            marker = "📌" if name == self.app.current_project_name else "  "
            
            answer += f"{marker} **{i}. {name}**\n"
            answer += f"      سکشن‌ها: {sections}  |  دستگاه‌ها: {devices}\n"
        
        return {
            'intent': 'list_projects',
            'data': {'count': len(projects)},
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }

    def _handle_count_projects(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «چند پروژه دارم؟»"""
        projects = self.app.projects
        
        # ===== آمار کلی =====
        total_projects = len(projects)
        total_revisions = sum(len(p.revisions) for p in projects.values())
        total_sections = sum(
            len(r.sections) 
            for p in projects.values() 
            for r in p.revisions
        )
        total_devices = sum(
            len(r.get_all_devices()) 
            for p in projects.values() 
            for r in p.revisions
        )
        
        # ===== ساخت پاسخ =====
        answer = f"📊 **آمار کلی پروژه‌ها**\n\n"
        answer += f"**تعداد پروژه‌ها:** {total_projects}\n"
        answer += f"**تعداد Revision ها:** {total_revisions}\n"
        answer += f"**تعداد سکشن‌ها:** {total_sections}\n"
        answer += f"**تعداد دستگاه‌ها:** {total_devices}\n\n"
        
        answer += "**📁 لیست پروژه‌ها:**\n"
        for i, (name, project) in enumerate(projects.items(), 1):
            current_rev = project.get_current_revision()
            sections = len(current_rev.sections) if current_rev else 0
            devices = len(current_rev.get_all_devices()) if current_rev else 0
            marker = "📌" if name == self.app.current_project_name else "  "
            answer += f"{marker} {i}. **{name}** ({sections} سکشن، {devices} دستگاه)\n"
        
        return {
            'intent': 'count_projects',
            'data': {
                'total_projects': total_projects,
                'total_revisions': total_revisions,
                'total_sections': total_sections,
                'total_devices': total_devices,
            },
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }

    def _handle_total_io(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «کل I/O پروژه X»"""
        groups = parsed['groups']
        project_name_raw = groups[0].strip().strip('"\'').strip() if groups else None
        
        # ===== ✅ تطبیق هوشمند =====
        project_name = None
        if project_name_raw:
            matched_name, confidence, method = self._resolve_project_name(project_name_raw)
            
            if matched_name:
                project_name = matched_name
                logger.info(
                    f"✅ Matched '{project_name_raw}' → '{project_name}' "
                    f"(via {method}, {confidence:.0%})"
                )
            else:
                project_name = project_name_raw
        
        # ===== اگر پروژه مشخص نشد =====
        if not project_name:
            project = self.app.get_current_project()
            if not project:
                return self._no_project_response()
            project_name = project.name
        
        project = self.app.projects.get(project_name)
        if not project:
            return self._project_not_found(project_name)
        
        current_rev = project.get_current_revision()
        if not current_rev:
            return self._no_revision_response(project_name)
        
        stats = current_rev.get_statistics()
        
        answer = f"📊 **I/O پروژه {project.name}**\n\n"
        answer += f"| نوع | تعداد |\n"
        answer += f"|-----|-------|\n"
        answer += f"| DI | {stats['total_di']} |\n"
        answer += f"| DO | {stats['total_do']} |\n"
        answer += f"| AI | {stats['total_ai']} |\n"
        answer += f"| AO | {stats['total_ao']} |\n"
        answer += f"| **مجموع** | **{stats['total_io']}** |\n"
        
        return {
            'intent': 'total_io',
            'data': stats,
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }

    def _handle_search_devices(self, parsed: Dict) -> Dict[str, Any]:
        """پاسخ به «دستگاه‌هایی که X دارند»"""
        groups = parsed['groups']
        component_name = groups[0] if groups else None
        component_key = normalize_component(component_name) if component_name else None
        
        if not component_key:
            return self._general_error(f"کامپوننت '{component_name}' شناسایی نشد")
        
        # ===== جستجو در همه پروژه‌ها =====
        matches = []
        current_project = self.app.get_current_project()
        
        if current_project:
            current_rev = current_project.get_current_revision()
            if current_rev:
                for device in current_rev.get_all_devices():
                    qty = getattr(device, component_key, 0)
                    if qty > 0:
                        matches.append({
                            'name': device.Name or 'Unnamed',
                            'qty': qty,
                            'description': device.Description or '',
                        })
        
        answer = f"🔍 **دستگاه‌های دارای {component_key} در پروژه فعلی**\n\n"
        answer += f"**تعداد کل:** {len(matches)}\n\n"
        
        for m in matches[:20]:
            answer += f"  • **{m['name']}** — {m['qty']} عدد"
            if m['description']:
                answer += f" ({m['description']})"
            answer += "\n"
        
        if len(matches) > 20:
            answer += f"\n... و {len(matches) - 20} دستگاه دیگر"
        
        return {
            'intent': 'search_devices',
            'data': {'component': component_key, 'count': len(matches)},
            'context': answer,
            'can_answer_directly': True,
            'direct_answer': answer,
        }
    
    def _handle_general_question(self, question: str) -> Dict[str, Any]:
        """سوال عمومی → ارسال به AI با Context خلاصه"""
        # ===== ساخت Context کلی =====
        project = self.app.get_current_project()
        
        if not project:
            context = "کاربر پروژه‌ای انتخاب نکرده است."
        else:
            current_rev = project.get_current_revision()
            if current_rev:
                stats = current_rev.get_statistics()
                context = f"""
پروژه فعلی: {project.name}
Revision: {current_rev.name}
تعداد سکشن: {stats['total_sections']}
تعداد دستگاه: {stats['total_devices']}
مجموع I/O: {stats['total_io']}
"""
            else:
                context = f"پروژه {project.name} هیچ Revision فعالی ندارد."
        
        return {
            'intent': 'general',
            'data': {},
            'context': context,
            'can_answer_directly': False,
            'direct_answer': None,
        }
    
    # ================================================================
    # HELPERS
    # ================================================================
    
    def _get_component_label(self, key: str, lang: str = 'en') -> str:
        """دریافت برچسب کامپوننت"""
        try:
            from core.constants import COMPONENT_LABELS
            return COMPONENT_LABELS.get(key, {}).get(lang, key)
        except:
            return key
    
    def _no_project_response(self) -> Dict[str, Any]:
        return {
            'intent': 'error',
            'data': {},
            'context': "پروژه‌ای انتخاب نشده.",
            'can_answer_directly': True,
            'direct_answer': "❌ لطفاً ابتدا یک پروژه انتخاب کنید.",
        }
    
    def _project_not_found(self, name: str) -> Dict[str, Any]:
        return {
            'intent': 'error',
            'data': {},
            'context': f"پروژه '{name}' یافت نشد.",
            'can_answer_directly': True,
            'direct_answer': f"❌ پروژه '{name}' پیدا نشد.",
        }
    
    def _no_revision_response(self, project_name: str) -> Dict[str, Any]:
        return {
            'intent': 'error',
            'data': {},
            'context': f"پروژه '{project_name}' Revision فعال ندارد.",
            'can_answer_directly': True,
            'direct_answer': f"❌ پروژه '{project_name}' هیچ Revision فعالی ندارد.",
        }
    
    def _general_error(self, msg: str) -> Dict[str, Any]:
        return {
            'intent': 'error',
            'data': {},
            'context': msg,
            'can_answer_directly': True,
            'direct_answer': f"❌ {msg}",
        }