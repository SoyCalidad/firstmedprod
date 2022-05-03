# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = "account.move"

	# name = fields.Char(compute="_compute_name_by_sequence")

	@api.depends('posted_before', 'state', 'journal_id', 'date', 'l10n_latam_document_type_id', 'journal_id.is_sequence')
	def _compute_name(self):
		""" Change the way that the use_document moves name is computed:

		* If move use document but does not have document type selected then name = '/' to do not show the name.
		* If move use document and are numbered manually do not compute name at all (will be set manually)
		* If move use document and is in draft state and has not been posted before we restart name to '/' (this is
		   when we change the document type) """
		without_doc_type = self.filtered(lambda x: x.journal_id.l10n_latam_use_documents and not x.l10n_latam_document_type_id)
		manual_documents = self.filtered(lambda x: x.journal_id.l10n_latam_use_documents and x.l10n_latam_manual_document_number)
		(without_doc_type + manual_documents.filtered(lambda x: not x.name or x.name and x.state == 'draft' and not x.posted_before)).name = '/'
		# if we change document or journal and we are in draft and not posted, we clean number so that is recomputed in super
		self.filtered(
			lambda x: x.journal_id.l10n_latam_use_documents and x.l10n_latam_document_type_id
			and not x.l10n_latam_manual_document_number and x.state == 'draft' and not x.posted_before).name = '/'
		self = self - without_doc_type - manual_documents

		def journal_key(move):
			return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

		def date_key(move):
			return (move.date.year, move.date.month)

		grouped = defaultdict(  # key: journal_id, move_type
			lambda: defaultdict(  # key: first adjacent (date.year, date.month)
				lambda: {
					'records': self.env['account.move'],
					'format': False,
					'format_values': False,
					'reset': False
				}
			)
		)
		self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
		highest_name = self[0]._get_last_sequence() if self else False

		# Group the moves by journal and month
		for move in self:
			if not highest_name and move == self[0] and not move.posted_before and move.date:
				# In the form view, we need to compute a default sequence so that the user can edit
				# it. We only check the first move as an approximation (enough for new in form view)
				pass
			elif (move.name and move.name != '/') or move.state != 'posted':
				try:
					if not move.posted_before:
						move._constrains_date_sequence()
					# Has already a name or is not posted, we don't add to a batch
					continue
				except ValidationError:
					# Has never been posted and the name doesn't match the date: recompute it
					pass
			group = grouped[journal_key(move)][date_key(move)]
			if not group['records']:
				# Compute all the values needed to sequence this whole group
				move._set_next_sequence()
				group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
				if move.journal_id.is_sequence and not highest_name:
					group['format_values']['seq'] = move.journal_id.sequence_number_next or 1
				_logger.info(group['format_values'])
				group['reset'] = move._deduce_sequence_number_reset(move.name)
			group['records'] += move

		# Fusion the groups depending on the sequence reset and the format used because `seq` is
		# the same counter for multiple groups that might be spread in multiple months.
		final_batches = []
		for journal_group in grouped.values():
			journal_group_changed = True
			for date_group in journal_group.values():
				if (
					journal_group_changed
					or final_batches[-1]['format'] != date_group['format']
					or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
				):
					final_batches += [date_group]
					journal_group_changed = False
				elif date_group['reset'] == 'never':
					final_batches[-1]['records'] += date_group['records']
				elif (
					date_group['reset'] == 'year'
					and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
				):
					final_batches[-1]['records'] += date_group['records']
				else:
					final_batches += [date_group]

		# Give the name based on previously computed values
		for batch in final_batches:
			for move in batch['records']:
				move.name = batch['format'].format(**batch['format_values'])
				batch['format_values']['seq'] += 1
			batch['records']._compute_split_sequence()

		self.filtered(lambda m: not m.name).name = '/'
				

	@api.depends("state", "journal_id", "date")
	def _compute_name_by_sequence(self):
		for move in self:
			name = move.name or "/"
			if (
					move.state == "posted"
					and (not move.name or move.name == "/")
					and move.journal_id
					and move.journal_id.sequence_id
			):
				if (
						move.move_type in ("out_refund", "in_refund")
						and move.journal_id.type in ("sale", "purchase")
						and move.journal_id.refund_sequence
						and move.journal_id.refund_sequence_id
				):
					seq = move.journal_id.refund_sequence_id
				else:
					seq = move.journal_id.sequence_id
				name = seq.next_by_id(sequence_date=move.date)
			move.name = name

	def _constrains_date_sequence(self):
		return True

