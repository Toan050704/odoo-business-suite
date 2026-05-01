/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { useService } from "@web/core/utils/hooks";

class StatementListController extends ListController {
    setup() {
        super.setup();
        this.action = useService("action");
    }

    async onClickFilter() {
        const targetModel = this.props.resModel;
        const actionMap = {
            's2d.statement': 'hkd_statements.action_statements_wizard_s2d',
            's2c.statement': 'hkd_statements.action_statements_wizard_s2c',
            's2b.statement': 'hkd_statements.action_statements_wizard_s2b',
            's2e.statement': 'hkd_statements.action_statements_wizard_s2e',
        };
        const actionXmlId = actionMap[targetModel];
        if (actionXmlId) {
            await this.action.doAction(actionXmlId);
        }
    }
}

registry.category("views").add("s2d_list", {
    ...listView,
    Controller: StatementListController,
    buttonTemplate: "s2d.ListView.Buttons",
});

registry.category("views").add("s2c_list", {
    ...listView,
    Controller: StatementListController,
    buttonTemplate: "s2c.ListView.Buttons",
});

registry.category("views").add("s2b_list", {
    ...listView,
    Controller: StatementListController,
    buttonTemplate: "s2b.ListView.Buttons",
});

registry.category("views").add("s2e_list", {
    ...listView,
    Controller: StatementListController,
    buttonTemplate: "s2e.ListView.Buttons",
});