/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { PaymentScreen } from '@point_of_sale/app/screens/payment_screen/payment_screen';

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        if (order && !order.get_partner()) {
            await this._hkdAssignWalkInCustomer(order);
        }
        return await super.validateOrder(isForceValidate);
    },

    async _hkdAssignWalkInCustomer(order) {
        try {
            const partners = await this.env.services.orm.searchRead(
                'res.partner',
                [['hkd_pos_walkin', '=', true]],
                ['name'],
                { limit: 1 }
            );
            if (partners && partners.length) {
                order.set_partner(partners[0]);
            }
        } catch (error) {
            console.warn('HKD POS: cannot auto-assign walk-in customer', error);
        }
    },
});
