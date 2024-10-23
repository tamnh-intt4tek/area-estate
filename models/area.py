from odoo import models, fields, api
from odoo.exceptions import UserError
from unidecode import unidecode
import logging

_logger = logging.getLogger(__name__)

class Area(models.Model):
    _name = 'areas.area'
    _description = 'Areas Management'

    name = fields.Char(string='Area Name', required=True)
    avatar = fields.Binary("Avatar", attachment=True)

    # Thông tin địa chỉ
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        default=lambda self: self.env['res.country'].search([('code', '=', 'VN')], limit=1),
        domain="[('name', '=', 'Vietnam')]"
    )
    province_id = fields.Many2one(
        'res.country.state',
        string='Province/City',
    )
    district_id = fields.Many2one(
        'res.country.district',
        string='District',
    )
    ward_id = fields.Many2one(
        'res.country.ward',
        string='Ward',
    )
    location = fields.Text(
        string='Location',
        help='Google Map location URL generated automatically based on the address.'
    )

    blog_id = fields.Many2one('blog.post', string='Website')
    description = fields.Html(string='Description')    
    image = fields.Binary("Image", attachment=True)

    # Các thông tin bổ sung
    acreage = fields.Float(string='Diện tích')
    population = fields.Integer(string='Dân cư')
    construction_density = fields.Float(string='Mật độ xây dựng')
    utilities = fields.Text("Utilities", help="Các tiện ích")


    is_public = fields.Boolean(
    string='Public Area', 
    default=False, 
    groups='areas_in_country.group_areas_manager'
    )
    last_public = fields.Datetime(
        string="Last Public", 
        readonly=True, 
        help="Thời gian công khai gần nhất."
    )
    public_status = fields.Selection([
        ('new', 'Mới (Chờ duyệt)'),
        ('edited', 'Đã sửa (Chờ duyệt)'),
        ('approved', 'Đã duyệt')
    ], string="Trạng thái công khai", default='new', readonly=True)


    @api.model
    def create(self, vals):
        vals['public_status'] = 'new'
        record = super(Area, self).create(vals)
        self._update_blog_post(record)

        return record


    def write(self, vals):
        if 'is_public' not in vals and self.public_status == 'approved':
            vals['public_status'] = 'edited'
            
        result = super(Area, self).write(vals)

        for record in self:
            if record.public_status == 'approved':
                self._update_blog_post(record)

        return result


    def _update_blog_post(self, record):
        if record.blog_id:
            updated_info = f"""
            THÔNG TIN VỀ KHU VỰC: 
            - Diện tích: {record.acreage} ha 
            - Dân cư: {record.population} người 
            - Mật độ xây dựng: {record.construction_density} % 
            - Tiện ích:
            {record.utilities} ...
            """

            old_info_start = record.blog_id.content.find("THÔNG TIN VỀ KHU VỰC:")
            if old_info_start != -1:
                old_info_end = record.blog_id.content.find("...", old_info_start)
                if old_info_end == -1:
                    old_info_end = len(record.blog_id.content)

                content_without_old_info = (
                    record.blog_id.content[:old_info_start] +
                    record.blog_id.content[old_info_end:]
                )
            else:
                content_without_old_info = record.blog_id.content or ''

            new_content = updated_info.strip() + "\n\n" + content_without_old_info.strip()

            record.blog_id.write({'content': new_content})


    def action_public_area(self):
        for area in self:
            area.write({
                'is_public': True,
                'public_status': 'approved',
                'last_public': fields.Datetime.now(),
            })

            self._update_blog_post(area)


    def action_go_to_website(self):
        for record in self:
            self._update_blog_post(record)

            if record.blog_id:
                blog_category = record.blog_id.blog_id
                blog_post_slug = unidecode(record.blog_id.name.replace(" ", "-").lower())
                blog_category_slug = unidecode(blog_category.name.replace(" ", "-").lower())

                blog_url = f'/blog/{blog_category_slug}-{blog_category.id}/{blog_post_slug}-{record.blog_id.id}'
                return {
                    'type': 'ir.actions.act_url',
                    'url': blog_url,
                    'target': 'self',
                }
            else:
                _logger.warning("Không tìm thấy trang web!")
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'areas.area',
                    'view_mode': 'form',
                    'res_id': record.id,
                    'target': 'current',
                }

    
    def action_go_to_google_maps(self):
        for record in self:
            if record.location:
                return {
                    'type': 'ir.actions.act_url',
                    'url': record.location,
                    'target': 'new',
                }
            else:
                _logger.warning("Không tìm thấy vị trí trên Google Maps!")
                raise UserError("Vị trí không hợp lệ. Vui lòng kiểm tra lại địa chỉ.")


#last update, last public, filter public => ok
# public lưu dạng new, đã edit chờ duyệt, đã duyệt => ok
# Xem lại thông tin được public mới đưa qua blog post => ok
# 3 user 3 quyền kh sài của admin, quyền dạng select box