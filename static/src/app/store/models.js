/** @odoo-module */

import { Order, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
	// Override here
});
