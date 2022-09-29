from io import StringIO

from IPython.display import HTML, Javascript, display


def display_table(data: list[list], headers: list[str]):
    s = StringIO()
    s.writelines([
        '<table is="table-sortable">',
        '<thead>',
        '<tr>',
        *['<th>' + h + '</th>' for h in headers],
        '</tr>',
        '</thead>',
        '<tbody>',
    ])

    for row in data:
        s.writelines([
            '<tr>',
            *['<td>' + str(r) + '</td>' for r in row],
            '</tr>',
        ])

    s.writelines([
        '</tbody>',
        '</table>',
    ])

    display(HTML(s.getvalue()))


def init_tables():
    display(
        Javascript('''
class TableSortable extends HTMLTableElement {
    constructor() {
        super();
    }

    connectedCallback() {
        // called when the html element and descendants are ready
        this.addEventListener("click", this.on_click);
    }

    compareText(a, b) {
        if (a.key < b.key) { return -1; }
        else if (a.key > b.key) { return 1; }
        else { return 0; }
    }


    sortTable(col, fCmp) {
        // get the body element of the table as we like to analyze and shift rows around.
        let tbody = this.querySelector('tbody');

        // create a list of {key,value} elements to be sorted
        let data = [];
        tbody.querySelectorAll('tr').forEach(tr => {
            let key = tr.children[col].innerText.toLowerCase();
            let asNum = parseFloat(key);
            data.push({
                key: isNaN(asNum) ? key : -asNum,
                val: tr,
            })
        });
        // sort and apply to table in ascending order
        data.sort(fCmp).forEach(r => tbody.appendChild(r.val));
    }


    elementIndex(/** @type HTMLElement */parent, /** @type HTMLElement */node) {
        let idx = -1;
        if (parent && node) {
            let e = parent.firstElementChild;
            while (e) {
                idx++;
                if (e === node) { return (idx); }
                e = e.nextElementSibling;
            }
        }
        return (-1);
    }


    on_click(/** @type MouseEvent */e) {
        let target = /** @type HTMLElement */(e.target);

        if (target.tagName === 'TH') {
        let n = this.elementIndex(target.parentElement, target);
        this.sortTable(n, this.compareText);
        }
    }
}

customElements.define('table-sortable', TableSortable, { extends: 'table' });
'''))
