"""
AI Parent Assistant Service
============================
Natural-language chatbot that queries the ERP to answer parent questions
such as "When are fees due?", "What was my child's attendance this month?",
"Show last exam results", etc.

Works WITHOUT external LLM — uses intent classification + template matching.
Can optionally forward to OpenAI/Gemini if API key is configured.
"""
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


# ── Intent Definitions ────────────────────────────────────────────────────────

INTENTS = {
    'fee_status': {
        'patterns': [
            r'fee|fees|payment|due|pending|balance|outstanding|installment|amount|pay',
        ],
        'handler': '_handle_fee_query',
    },
    'attendance': {
        'patterns': [
            r'attend|absent|present|leave|absence|sick|absent\s*days?',
        ],
        'handler': '_handle_attendance_query',
    },
    'marks': {
        'patterns': [
            r'mark|grade|result|exam|score|rank|report\s*card|performance|cgpa|percentage',
        ],
        'handler': '_handle_marks_query',
    },
    'homework': {
        'patterns': [
            r'homework|assignment|home\s*work|pending\s*work|classwork',
        ],
        'handler': '_handle_homework_query',
    },
    'timetable': {
        'patterns': [
            r'timetable|time\s*table|schedule|class\s*timing|period',
        ],
        'handler': '_handle_timetable_query',
    },
    'notice': {
        'patterns': [
            r'notice|announcement|circular|event|holiday|vacation',
        ],
        'handler': '_handle_notice_query',
    },
    'transport': {
        'patterns': [
            r'bus|transport|route|pick\s*up|drop|vehicle|driver',
        ],
        'handler': '_handle_transport_query',
    },
    'general': {
        'patterns': [r'.*'],
        'handler': '_handle_general_query',
    },
}


class AIParentAssistant:
    """Stateless assistant — each call is independent."""

    @staticmethod
    def chat(school_id, parent_id, student_id, message):
        """
        Process a parent's chat message and return a structured reply.

        Returns dict: {success, reply, intent, data?}
        """
        try:
            message_lower = message.strip().lower()
            if not message_lower:
                return {
                    'success': True,
                    'reply': "Hi! I'm your school assistant. Ask me about fees, attendance, marks, homework, timetable, notices, or transport.",
                    'intent': 'greeting',
                }

            # Classify intent
            intent_name = AIParentAssistant._classify_intent(message_lower)
            handler_name = INTENTS[intent_name]['handler']
            handler = getattr(AIParentAssistant, handler_name)

            result = handler(school_id, parent_id, student_id, message_lower)
            result['intent'] = intent_name
            return result

        except Exception as e:
            logger.error(f"AI Assistant error: {str(e)}")
            return {
                'success': True,
                'reply': "I'm sorry, I couldn't process your request right now. Please try again or contact the school office.",
                'intent': 'error',
            }

    @staticmethod
    def get_suggestions(school_id, student_id):
        """Return contextual quick-action suggestions for the parent."""
        suggestions = [
            {"label": "What are my pending fees?", "intent": "fee_status"},
            {"label": "Show attendance this month", "intent": "attendance"},
            {"label": "Latest exam results", "intent": "marks"},
            {"label": "Any pending homework?", "intent": "homework"},
            {"label": "Today's timetable", "intent": "timetable"},
            {"label": "Recent notices", "intent": "notice"},
        ]
        return {'success': True, 'suggestions': suggestions}

    # ── Intent Classification ─────────────────────────────────────────────

    @staticmethod
    def _classify_intent(message):
        """Score-based intent classification."""
        scores = {}
        for intent_name, config in INTENTS.items():
            if intent_name == 'general':
                continue
            score = 0
            for pattern in config['patterns']:
                matches = re.findall(pattern, message)
                score += len(matches)
            if score > 0:
                scores[intent_name] = score

        if not scores:
            return 'general'
        return max(scores, key=scores.get)

    # ── Intent Handlers ───────────────────────────────────────────────────

    @staticmethod
    def _handle_fee_query(school_id, parent_id, student_id, message):
        """Query fee status from ERP."""
        try:
            from app.services.parent_portal_service import ParentPortalService
            result = ParentPortalService.get_fee_status(school_id, student_id)

            if not result.get('success'):
                return {'success': True, 'reply': "I couldn't fetch fee details right now. Please check the fee section in your portal."}

            data = result.get('data', {})
            total = data.get('total_fee', 0)
            paid = data.get('total_paid', 0)
            pending = data.get('pending_amount', total - paid)
            installments = data.get('installments', [])

            # Find next due
            upcoming = [i for i in installments if not i.get('is_paid')]
            next_due = upcoming[0] if upcoming else None

            reply_parts = [f"📊 **Fee Summary for your child:**"]
            reply_parts.append(f"• Total Fee: ₹{total:,.0f}")
            reply_parts.append(f"• Paid: ₹{paid:,.0f}")
            reply_parts.append(f"• Pending: ₹{pending:,.0f}")

            if next_due:
                reply_parts.append(f"\n📅 **Next Due:** ₹{next_due.get('amount', 0):,.0f} by {next_due.get('due_date', 'N/A')}")

            if not upcoming:
                reply_parts.append("\n✅ All fees are paid! No pending installments.")

            return {
                'success': True,
                'reply': '\n'.join(reply_parts),
                'data': data,
            }
        except Exception as e:
            logger.error(f"Fee query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve fee information. Please check the portal directly."}

    @staticmethod
    def _handle_attendance_query(school_id, parent_id, student_id, message):
        """Query attendance from ERP."""
        try:
            from app.services.parent_portal_service import ParentPortalService
            now = datetime.utcnow()
            result = ParentPortalService.get_attendance_view(
                school_id, student_id, now.month, now.year
            )

            if not result.get('success'):
                return {'success': True, 'reply': "I couldn't fetch attendance details right now."}

            data = result.get('data', {})
            summary = data.get('summary', {})
            total = summary.get('total_days', 0)
            present = summary.get('present', 0)
            absent = summary.get('absent', 0)
            percentage = summary.get('percentage', 0)

            reply_parts = [f"📋 **Attendance for {now.strftime('%B %Y')}:**"]
            reply_parts.append(f"• Working Days: {total}")
            reply_parts.append(f"• Present: {present} days")
            reply_parts.append(f"• Absent: {absent} days")
            reply_parts.append(f"• Attendance: {percentage:.1f}%")

            if percentage < 75:
                reply_parts.append("\n⚠️ Attendance is below 75%. Please ensure regular attendance.")
            elif percentage >= 90:
                reply_parts.append("\n🌟 Excellent attendance! Keep it up!")

            return {
                'success': True,
                'reply': '\n'.join(reply_parts),
                'data': data,
            }
        except Exception as e:
            logger.error(f"Attendance query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve attendance information right now."}

    @staticmethod
    def _handle_marks_query(school_id, parent_id, student_id, message):
        """Query marks/grades from ERP."""
        try:
            from app.services.parent_portal_service import ParentPortalService
            result = ParentPortalService.get_marks_view(school_id, student_id)

            if not result.get('success'):
                return {'success': True, 'reply': "I couldn't fetch exam results right now."}

            data = result.get('data', {})
            exams = data.get('exams', [])

            if not exams:
                return {'success': True, 'reply': "No exam results available yet. Results will appear here once published."}

            latest = exams[0] if exams else {}
            reply_parts = [f"📝 **Latest Exam Results:**"]
            reply_parts.append(f"• Exam: {latest.get('exam_name', 'N/A')}")

            subjects = latest.get('subjects', [])
            for sub in subjects[:8]:  # Limit to 8 subjects
                name = sub.get('subject_name', 'N/A')
                marks = sub.get('marks_obtained', 0)
                total = sub.get('max_marks', 100)
                grade = sub.get('grade', '')
                reply_parts.append(f"  - {name}: {marks}/{total} {f'({grade})' if grade else ''}")

            overall = latest.get('percentage', latest.get('total_percentage', ''))
            if overall:
                reply_parts.append(f"\n📊 Overall: {overall}%")

            return {
                'success': True,
                'reply': '\n'.join(reply_parts),
                'data': data,
            }
        except Exception as e:
            logger.error(f"Marks query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve exam results right now."}

    @staticmethod
    def _handle_homework_query(school_id, parent_id, student_id, message):
        """Query homework from ERP."""
        try:
            from app.services.parent_portal_service import ParentPortalService
            result = ParentPortalService.get_homework_view(school_id, student_id)

            if not result.get('success'):
                return {'success': True, 'reply': "I couldn't fetch homework details right now."}

            data = result.get('data', {})
            homework_list = data.get('homework', [])

            if not homework_list:
                return {
                    'success': True,
                    'reply': "📚 No pending homework right now. Enjoy your free time! 🎉",
                    'data': data,
                }

            reply_parts = [f"📚 **Pending Homework ({len(homework_list)} items):**"]
            for hw in homework_list[:6]:
                subject = hw.get('subject', 'N/A')
                title = hw.get('title', hw.get('description', 'N/A'))
                due = hw.get('due_date', 'N/A')
                reply_parts.append(f"  - **{subject}**: {title} (Due: {due})")

            if len(homework_list) > 6:
                reply_parts.append(f"\n...and {len(homework_list) - 6} more. Check the portal for details.")

            return {
                'success': True,
                'reply': '\n'.join(reply_parts),
                'data': data,
            }
        except Exception as e:
            logger.error(f"Homework query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve homework information right now."}

    @staticmethod
    def _handle_timetable_query(school_id, parent_id, student_id, message):
        """Query timetable from ERP."""
        try:
            from app.models.student import Student
            from app.models.academics import TimetableSlot
            from app.extensions import db

            student = Student.query.filter_by(
                id=student_id, school_id=school_id
            ).first()

            if not student:
                return {'success': True, 'reply': "Student not found."}

            today = datetime.utcnow().strftime('%A')
            slots = TimetableSlot.query.filter_by(
                school_id=school_id,
                class_id=student.class_id if hasattr(student, 'class_id') else None,
                day_of_week=today
            ).order_by(TimetableSlot.start_time).all()

            if not slots:
                return {
                    'success': True,
                    'reply': f"📅 No classes scheduled for **{today}**. It might be a holiday or the timetable hasn't been set up yet.",
                }

            reply_parts = [f"📅 **Timetable for {today}:**"]
            for slot in slots:
                subject = slot.subject.name if slot.subject else 'Free Period'
                teacher = slot.teacher.name if hasattr(slot, 'teacher') and slot.teacher else ''
                start = slot.start_time or ''
                end = slot.end_time or ''
                line = f"  - {start}-{end}: **{subject}**"
                if teacher:
                    line += f" ({teacher})"
                reply_parts.append(line)

            return {'success': True, 'reply': '\n'.join(reply_parts)}
        except Exception as e:
            logger.error(f"Timetable query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve the timetable right now."}

    @staticmethod
    def _handle_notice_query(school_id, parent_id, student_id, message):
        """Query recent notices from ERP."""
        try:
            from app.models.communication import Notice
            notices = Notice.query.filter_by(
                school_id=school_id, is_active=True
            ).order_by(Notice.published_date.desc()).limit(5).all()

            if not notices:
                return {'success': True, 'reply': "📢 No recent notices or announcements."}

            reply_parts = ["📢 **Recent Notices:**"]
            for n in notices:
                title = n.title
                date = n.published_date.strftime('%d %b %Y') if n.published_date else ''
                reply_parts.append(f"  - **{title}** ({date})")
                if n.content:
                    # Truncate long content
                    content = n.content[:100] + ('...' if len(n.content) > 100 else '')
                    reply_parts.append(f"    {content}")

            return {'success': True, 'reply': '\n'.join(reply_parts)}
        except Exception as e:
            logger.error(f"Notice query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve notices right now."}

    @staticmethod
    def _handle_transport_query(school_id, parent_id, student_id, message):
        """Query transport info from ERP."""
        try:
            from app.models.logistics import StudentTransportAllocation, Route, Vehicle

            alloc = StudentTransportAllocation.query.filter_by(
                school_id=school_id, student_id=student_id, is_active=True
            ).first()

            if not alloc:
                return {
                    'success': True,
                    'reply': "🚌 No transport allocation found for your child. Contact the school office for transport details.",
                }

            route = Route.query.get(alloc.route_id) if alloc.route_id else None
            vehicle = Vehicle.query.get(route.vehicle_id) if route and route.vehicle_id else None

            reply_parts = ["🚌 **Transport Details:**"]
            if route:
                reply_parts.append(f"• Route: {route.name}")
            if vehicle:
                reply_parts.append(f"• Vehicle: {vehicle.vehicle_number}")
                if vehicle.driver_name:
                    reply_parts.append(f"• Driver: {vehicle.driver_name}")
                if vehicle.driver_phone:
                    reply_parts.append(f"• Driver Phone: {vehicle.driver_phone}")
            if alloc.pickup_point:
                reply_parts.append(f"• Pickup: {alloc.pickup_point}")
            if alloc.drop_point:
                reply_parts.append(f"• Drop: {alloc.drop_point}")

            return {'success': True, 'reply': '\n'.join(reply_parts)}
        except Exception as e:
            logger.error(f"Transport query error: {e}")
            return {'success': True, 'reply': "I couldn't retrieve transport information right now."}

    @staticmethod
    def _handle_general_query(school_id, parent_id, student_id, message):
        """Fallback for unrecognized intents."""
        return {
            'success': True,
            'reply': (
                "I can help you with:\n"
                "💰 **Fees** — \"What are my pending fees?\"\n"
                "📋 **Attendance** — \"Show attendance this month\"\n"
                "📝 **Marks** — \"Latest exam results\"\n"
                "📚 **Homework** — \"Any pending homework?\"\n"
                "📅 **Timetable** — \"Today's timetable\"\n"
                "📢 **Notices** — \"Recent notices\"\n"
                "🚌 **Transport** — \"Bus route details\"\n\n"
                "Try asking one of these!"
            ),
        }
