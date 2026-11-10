var Gt = Object.defineProperty;
var Kt = (a, i, n) => i in a ? Gt(a, i, { enumerable: !0, configurable: !0, writable: !0, value: n }) : a[i] = n;
var Xe = (a, i, n) => Kt(a, typeof i != "symbol" ? i + "" : i, n);
import { jsx as t, jsxs as m, Fragment as fe } from "react/jsx-runtime";
import { useShell as ve, defineSection as Xt } from "@stelden/seal-frontend/section";
import { useContext as Zt, createContext as Qt, forwardRef as it, createElement as $e, useCallback as be, useState as E, useMemo as ce, useRef as Re, useEffect as ye } from "react";
import { useParams as Z, useSearchParams as rt } from "react-router";
import { useGet as N, usePost as q, formatDateTime as xe, formatDate as g, uploadFile as st, formatCurrency as B, useFrappeCall as en } from "@stelden/seal-frontend";
import { z as le, required as we, frappeDate as _e, useSealForm as de, SealForm as ue, RadioInput as lt, DateInput as re, CheckboxInput as ct, TextInput as U, FormActions as he, SelectInput as Ae, FormSection as Ze, AutocompleteInput as De, FileInput as dt, MobileInputKE as tn, amount as ut, RowsInput as ht, NumberInput as je } from "@stelden/seal-frontend/forms";
import { toneMap as nn, StatusChip as an, __ as e, useNotify as V, FormPage as te, Alert as $, Button as w, Text as ee, Section as F, List as L, ListItem as M, ListPage as ne, EmptyState as ae, DetailPage as Q, DescriptionList as J, TabsNav as on, TabPanel as Se, SealDialog as mt, Textarea as rn, ConfirmDialog as pt, DashboardPage as sn, StatGrid as yt, StatCard as Ee, Badge as ge, FilterChips as ln, Label as Ce, Input as qe, IconButton as Le, Card as cn, CardContent as dn, Select as un } from "@stelden/seal-frontend/ui";
const X = (a) => encodeURIComponent(a);
function oe(a) {
  if (!a) return "";
  try {
    return decodeURIComponent(a);
  } catch {
    return a;
  }
}
const l = {
  leave: "leave",
  leaveNew: "leave/new",
  leaveRecord: (a) => `leave/${X(a)}`,
  cover: "cover",
  handover: (a) => `cover/${X(a)}`,
  toil: "toil",
  toilNew: "toil/new",
  toilRecord: (a) => `toil/${X(a)}`,
  timesheet: "timesheet",
  week: (a) => `timesheet/week/${a}`,
  timesheetRecord: (a) => `timesheet/${X(a)}`,
  expenses: "expenses",
  expenseNew: "expenses/new",
  expenseRecord: (a) => `expenses/${X(a)}`,
  advances: "advances",
  advanceNew: "advances/new",
  advanceRecord: (a) => `advances/${X(a)}`,
  pay: "pay",
  payRecord: (a) => `pay/${X(a)}`,
  checkIn: "check-in",
  attendance: "attendance",
  attendanceNew: "attendance/new",
  attendanceRecord: (a) => `attendance/${X(a)}`,
  shifts: "shifts",
  shiftNew: "shifts/new",
  shiftRecord: (a) => `shifts/${X(a)}`,
  me: "me",
  payoutNew: "me/payout/new",
  payoutRecord: (a) => `me/payout/${X(a)}`
}, ft = {
  "Leave Application": { list: l.leave, record: l.leaveRecord, create: l.leaveNew },
  "Leave Allocation": { list: l.leave },
  "Task Assignment": { list: l.cover, record: l.handover },
  "Time Off in Lieu Claim": { list: l.toil, record: l.toilRecord, create: l.toilNew },
  Timesheet: { list: l.timesheet, record: l.timesheetRecord },
  "Expense Claim": { list: l.expenses, record: l.expenseRecord, create: l.expenseNew },
  "Employee Advance": { list: l.advances, record: l.advanceRecord, create: l.advanceNew },
  "Salary Slip": { list: l.pay, record: l.payRecord },
  Employee: { list: l.me, record: () => l.me },
  "Employee Checkin": { list: l.checkIn, record: () => l.checkIn, create: l.checkIn },
  "Attendance Request": { list: l.attendance, record: l.attendanceRecord, create: l.attendanceNew },
  "Shift Request": { list: l.shifts, record: l.shiftRecord, create: l.shiftNew },
  "Employee Dependent and Beneficiary": { list: l.me, record: () => l.me },
  "Payout Change Request": { list: l.me, record: l.payoutRecord, create: l.payoutNew }
};
function hn(a) {
  return ft[a]?.list;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const mn = (a) => a?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function pn(a, i, n = []) {
  if (i == null)
    throw new Error("[lucide]: iconNode is required when icon name is used");
  return {
    name: mn(a),
    size: 24,
    node: i,
    ...n.length > 0 ? { aliases: n } : {}
  };
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const yn = (a) => {
  let i = "", n = !1;
  for (const o of a) {
    if (o === "-" || o === "_" || o <= " ") {
      n = i.length > 0;
      continue;
    }
    i.length === 0 ? i += o.toLowerCase() : i += n ? o.toUpperCase() : o, n = !1;
  }
  return i;
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const fn = (a) => {
  const i = yn(a);
  return i.charAt(0).toUpperCase() + i.slice(1);
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Te = (...a) => a.filter((i, n, o) => !!i && i.trim() !== "" && o.indexOf(i) === n).join(" ").trim();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const se = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": 2,
  "stroke-linecap": "round",
  "stroke-linejoin": "round"
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function Me(a) {
  return a != null;
}
function vn(a, i = {}) {
  const n = i.attributeNames ?? {}, o = (h) => n[h] ?? h, s = a.size ?? a.width ?? se.width, c = a.size ?? a.height ?? se.height, r = a.aliases?.filter((h) => typeof h == "string" && h.trim() !== "").map((h) => `lucide-${h}`) ?? [], u = [...a.name ? [`lucide-${a.name}`] : [], ...r], p = i.className?.split(" ").filter(Boolean) ?? [], v = i.includeDefaultClasses === !1 ? Te(...p) : Te("lucide", ...u, ...p), y = i.absoluteStrokeWidth ? Number(i.strokeWidth ?? se["stroke-width"]) * Number(a.size ?? a.width ?? se.width) / Number(i.size ?? i.width ?? se.width) : i.strokeWidth ?? se["stroke-width"];
  return [
    "svg",
    {
      ...Object.entries(se).reduce((h, [R, x]) => (h[o(R)] = x, h), {}),
      ..."color" in i && i.color && {
        [o("stroke")]: i.color
      },
      ..."size" in i && Me(i.size) && {
        [o("width")]: i.size,
        [o("height")]: i.size
      },
      ..."width" in i && Me(i.width) && {
        [o("width")]: i.width
      },
      ..."height" in i && Me(i.height) && {
        [o("height")]: i.height
      },
      [o("stroke-width")]: y,
      ...v && {
        [o("class")]: v
      },
      [o("viewBox")]: `0 0 ${s} ${c}`,
      ...i.hasA11yProp === !1 ? {
        [o("aria-hidden")]: "true"
      } : {},
      ..."attributes" in i && i.attributes
    },
    a.node.map((h) => {
      const [R, x, W] = h, S = i.nonScalingStroke ? { [o("vector-effect")]: "non-scaling-stroke", ...x } : x;
      return W ? [R, S, W] : [R, S];
    })
  ];
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function gn(a, i = {}) {
  return vn(a, {
    ...i,
    attributeNames: {
      ...i.attributeNames,
      class: "className",
      "stroke-width": "strokeWidth",
      "stroke-linecap": "strokeLinecap",
      "stroke-linejoin": "strokeLinejoin",
      "vector-effect": "vectorEffect"
    }
  });
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const _n = (a) => {
  for (const i in a)
    if (i.startsWith("aria-") || i === "role" || i === "title")
      return !0;
  return !1;
}, kn = Qt({}), wn = () => Zt(kn), bn = it(
  ({
    color: a,
    size: i,
    width: n,
    height: o,
    strokeWidth: s,
    absoluteStrokeWidth: c,
    nonScalingStroke: r,
    className: u = "",
    children: p,
    iconNode: v = [],
    icon: y = {
      node: v,
      aliases: [],
      size: 24
    },
    ...d
  }, h) => {
    const {
      size: R = 24,
      strokeWidth: x = 2,
      absoluteStrokeWidth: W = !1,
      nonScalingStroke: S = !1,
      color: A = "currentColor",
      className: P = ""
    } = wn() ?? {}, j = !!p || _n(d), [I, G, O = []] = gn(y, {
      color: a ?? A,
      width: n ?? i ?? R,
      height: o ?? i ?? R,
      strokeWidth: s ?? x,
      absoluteStrokeWidth: c ?? W,
      nonScalingStroke: r ?? S,
      className: Te(P, u),
      hasA11yProp: j,
      attributes: d
    });
    return $e(
      I,
      {
        ref: h,
        ...G
      },
      [
        ...O.map(([_, k]) => $e(_, k)),
        ...Array.isArray(p) ? p : [p]
      ]
    );
  }
);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function H(a, i = [], n = []) {
  const o = typeof a == "string" ? pn(a, i, n) : a, s = it(
    ({ className: c, ...r }, u) => $e(bn, {
      ref: u,
      icon: o,
      className: c,
      ...r
    })
  );
  return o.name && (s.displayName = fn(o.name)), s;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const vt = {
  name: "calendar-days",
  size: 24,
  node: [
    ["path", { d: "M8 2v3", key: "1ioesn" }],
    ["path", { d: "M16 2v3", key: "otl347" }],
    ["rect", { x: "3", y: "3", width: "18", height: "18", rx: "2", key: "h1oib" }],
    ["path", { d: "M3 9h18", key: "1pudct" }],
    ["path", { d: "M8 13h.01", key: "1sbv64" }],
    ["path", { d: "M12 13h.01", key: "y0uutt" }],
    ["path", { d: "M16 13h.01", key: "wip0gl" }],
    ["path", { d: "M8 17h.01", key: "p3bg7i" }],
    ["path", { d: "M12 17h.01", key: "p32p05" }],
    ["path", { d: "M16 17h.01", key: "ql8jdd" }]
  ]
};
vt.node;
const He = H(vt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const gt = {
  name: "chevron-left",
  size: 24,
  node: [["path", { d: "m15 18-6-6 6-6", key: "1wnfg3" }]]
};
gt.node;
const Cn = H(gt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const _t = {
  name: "chevron-right",
  size: 24,
  node: [["path", { d: "m9 18 6-6-6-6", key: "mthhwq" }]]
};
_t.node;
const kt = H(_t);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const wt = {
  name: "clock",
  size: 24,
  node: [
    ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
    ["path", { d: "M12 6v6l4 2", key: "mmk7yg" }]
  ]
};
wt.node;
const Be = H(wt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const bt = {
  name: "copy",
  size: 24,
  node: [
    ["rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2", key: "17jyea" }],
    ["path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2", key: "zix9uf" }]
  ]
};
bt.node;
const Rn = H(bt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ct = {
  name: "download",
  size: 24,
  node: [
    ["path", { d: "M12 15V3", key: "m9g1x1" }],
    ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
    ["path", { d: "m7 10 5 5 5-5", key: "brsn70" }]
  ]
};
Ct.node;
const xn = H(Ct);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Rt = {
  name: "file-clock",
  size: 24,
  node: [
    [
      "path",
      {
        d: "M16 22h2a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v2.85",
        key: "ryk6xj"
      }
    ],
    ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }],
    ["path", { d: "M8 14v2.2l1.6 1", key: "6m4bie" }],
    ["circle", { cx: "8", cy: "16", r: "6", key: "10v15b" }]
  ]
};
Rt.node;
const An = H(Rt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const xt = {
  name: "fingerprint-pattern",
  size: 24,
  node: [
    ["path", { d: "M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4", key: "1nerag" }],
    ["path", { d: "M14 13.12c0 2.38 0 6.38-1 8.88", key: "o46ks0" }],
    ["path", { d: "M17.29 21.02c.12-.6.43-2.3.5-3.02", key: "ptglia" }],
    ["path", { d: "M2 12a10 10 0 0 1 18-6", key: "ydlgp0" }],
    ["path", { d: "M2 16h.01", key: "1gqxmh" }],
    ["path", { d: "M21.8 16c.2-2 .131-5.354 0-6", key: "drycrb" }],
    ["path", { d: "M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2", key: "1tidbn" }],
    ["path", { d: "M8.65 22c.21-.66.45-1.32.57-2", key: "13wd9y" }],
    ["path", { d: "M9 6.8a6 6 0 0 1 9 5.2v2", key: "1fr1j5" }]
  ],
  aliases: ["fingerprint"]
};
xt.node;
const Qe = H(xt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const At = {
  name: "hand-coins",
  size: 24,
  node: [
    ["path", { d: "M11 15h2a2 2 0 1 0 0-4h-3c-.6 0-1.1.2-1.4.6L3 17", key: "geh8rc" }],
    [
      "path",
      {
        d: "m7 21 1.6-1.4c.3-.4.8-.6 1.4-.6h4c1.1 0 2.1-.4 2.8-1.2l4.6-4.4a2 2 0 0 0-2.75-2.91l-4.2 3.9",
        key: "1fto5m"
      }
    ],
    ["path", { d: "m2 16 6 6", key: "1pfhp9" }],
    ["circle", { cx: "16", cy: "9", r: "2.9", key: "1n0dlu" }],
    ["circle", { cx: "6", cy: "5", r: "3", key: "151irh" }]
  ]
};
At.node;
const Nt = H(At);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Dt = {
  name: "hourglass",
  size: 24,
  node: [
    ["path", { d: "M5 22h14", key: "ehvnwv" }],
    ["path", { d: "M5 2h14", key: "pdyrp9" }],
    [
      "path",
      {
        d: "M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22",
        key: "1d314k"
      }
    ],
    [
      "path",
      {
        d: "M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2",
        key: "1vvvr6"
      }
    ]
  ]
};
Dt.node;
const Pe = H(Dt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const St = {
  name: "id-card",
  size: 24,
  node: [
    ["path", { d: "M13 19a4 4 0 00-8 0", key: "cugzd5" }],
    ["path", { d: "M16 10h2", key: "8sgtl7" }],
    ["path", { d: "M16 14h2", key: "epxaof" }],
    ["circle", { cx: "9", cy: "12", r: "3", key: "u3jwor" }],
    ["rect", { x: "2", y: "5", width: "20", height: "14", rx: "2", key: "qneu4z" }]
  ]
};
St.node;
const Nn = H(St);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Lt = {
  name: "log-in",
  size: 24,
  node: [
    ["path", { d: "m10 17 5-5-5-5", key: "1bsop3" }],
    ["path", { d: "M15 12H3", key: "6jk70r" }],
    ["path", { d: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4", key: "u53s6r" }]
  ]
};
Lt.node;
const Dn = H(Lt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Mt = {
  name: "log-out",
  size: 24,
  node: [
    ["path", { d: "m16 17 5-5-5-5", key: "1bji2h" }],
    ["path", { d: "M21 12H9", key: "dn1m92" }],
    ["path", { d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", key: "1uf3rs" }]
  ]
};
Mt.node;
const Sn = H(Mt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Wt = {
  name: "map-pin",
  size: 24,
  node: [
    [
      "path",
      {
        d: "M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",
        key: "1r0f0z"
      }
    ],
    ["circle", { cx: "12", cy: "10", r: "3", key: "ilqhr7" }]
  ]
};
Wt.node;
const Ye = H(Wt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const $t = {
  name: "plus",
  size: 24,
  node: [
    ["path", { d: "M5 12h14", key: "1ays0h" }],
    ["path", { d: "M12 5v14", key: "s699le" }]
  ]
};
$t.node;
const me = H($t);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Et = {
  name: "receipt",
  size: 24,
  node: [
    ["path", { d: "M12 17V7", key: "pyj7ub" }],
    ["path", { d: "M16 8h-6a2 2 0 0 0 0 4h4a2 2 0 0 1 0 4H8", key: "1elt7d" }],
    [
      "path",
      {
        d: "M4 3a1 1 0 0 1 1-1 1.3 1.3 0 0 1 .7.2l.933.6a1.3 1.3 0 0 0 1.4 0l.934-.6a1.3 1.3 0 0 1 1.4 0l.933.6a1.3 1.3 0 0 0 1.4 0l.933-.6a1.3 1.3 0 0 1 1.4 0l.934.6a1.3 1.3 0 0 0 1.4 0l.933-.6A1.3 1.3 0 0 1 19 2a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1 1.3 1.3 0 0 1-.7-.2l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.934.6a1.3 1.3 0 0 1-1.4 0l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-1.4 0l-.934-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-.7.2 1 1 0 0 1-1-1z",
        key: "ycz6yz"
      }
    ]
  ]
};
Et.node;
const Fe = H(Et);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const qt = {
  name: "repeat",
  size: 24,
  node: [
    ["path", { d: "m17 2 4 4-4 4", key: "nntrym" }],
    ["path", { d: "M3 11v-1a4 4 0 0 1 4-4h14", key: "84bu3i" }],
    ["path", { d: "m7 22-4-4 4-4", key: "1wqhfi" }],
    ["path", { d: "M21 13v1a4 4 0 0 1-4 4H3", key: "1rx37r" }]
  ]
};
qt.node;
const Tt = H(qt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ht = {
  name: "trash",
  size: 24,
  node: [
    ["path", { d: "M10 11v6", key: "nco0om" }],
    ["path", { d: "M14 11v6", key: "outv1u" }],
    ["path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6", key: "miytrc" }],
    ["path", { d: "M3 6h18", key: "d0wm0j" }],
    ["path", { d: "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2", key: "e791ji" }]
  ],
  aliases: ["trash-2"]
};
Ht.node;
const Ln = H(Ht);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Bt = {
  name: "users",
  size: 24,
  node: [
    ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
    ["path", { d: "M16 3.128a4 4 0 0 1 0 7.744", key: "16gr8j" }],
    ["path", { d: "M22 21v-2a4 4 0 0 0-3-3.87", key: "kshegd" }],
    ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }]
  ]
};
Bt.node;
const Pt = H(Bt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ft = {
  name: "wallet",
  size: 24,
  node: [
    [
      "path",
      {
        d: "M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1",
        key: "18etb6"
      }
    ],
    ["path", { d: "M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4", key: "xoc0q4" }]
  ]
};
Ft.node;
const It = H(Ft), C = "seal_hrms.my_desk.api.", f = {
  home: `${C}home`,
  leaveList: `${C}leave_list`,
  leaveOptions: `${C}leave_options`,
  leaveRecord: `${C}leave_record`,
  applyForLeave: `${C}apply_for_leave`,
  colleagues: `${C}colleagues`,
  cover: `${C}cover`,
  handoverRecord: `${C}handover_record`,
  toilList: `${C}toil_list`,
  toilRecord: `${C}toil_record`,
  saveToilClaim: `${C}save_toil_claim`,
  toilAction: `${C}toil_action`,
  timesheets: `${C}timesheets`,
  timesheetWeek: `${C}timesheet_week`,
  timesheetRecord: `${C}timesheet_record`,
  saveTimesheetWeek: `${C}save_timesheet_week`,
  timesheetClaim: `${C}timesheet_claim`,
  expenseList: `${C}expense_list`,
  expenseOptions: `${C}expense_options`,
  expenseRecord: `${C}expense_record`,
  claimExpenses: `${C}claim_expenses`,
  advanceList: `${C}advance_list`,
  advanceRecord: `${C}advance_record`,
  requestAdvance: `${C}request_advance`,
  payslips: `${C}payslips`,
  payslipRecord: `${C}payslip_record`,
  payslipPdf: `${C}payslip_pdf`,
  checkinStatus: `${C}checkin_status`,
  checkIn: `${C}check_in`,
  attendanceRequests: `${C}attendance_requests`,
  attendanceOptions: `${C}attendance_options`,
  attendanceRecord: `${C}attendance_record`,
  requestAttendance: `${C}request_attendance`,
  requestShift: `${C}request_shift`,
  myDetails: `${C}my_details`,
  updateMyContact: `${C}update_my_contact`,
  payoutOptions: `${C}payout_options`,
  requestPayoutChange: `${C}request_payout_change`,
  setPayoutEvidence: `${C}set_payout_evidence`,
  payoutRequestRecord: `${C}payout_request_record`,
  // seal_hrms' own endpoints, the same the desk calls.
  respond: "seal_hrms.seal_hrms.task_assignment_actions.respond",
  respondAuthority: "seal_hrms.seal_hrms.task_assignment_actions.respond_authority",
  addNote: "seal_hrms.seal_hrms.task_assignment_actions.add_note",
  returnNote: "seal_hrms.seal_hrms.task_assignment_actions.leave_return_note",
  returnWork: "seal_hrms.seal_hrms.task_assignment_actions.return_work",
  extraTime: "seal_hrms.seal_hrms.toil.evidence.get_extra_time",
  sendPayoutChange: "seal_hrms.seal_hrms.payout_change.send",
  withdrawPayoutChange: "seal_hrms.seal_hrms.payout_change.withdraw"
};
function Mn(a) {
  return `/api/method/${f.payslipPdf}?name=${encodeURIComponent(a)}`;
}
function D() {
  const a = ve();
  return be((i) => a.navigate(i), [a]);
}
const Wn = nn(
  {
    Open: "info",
    Draft: "default",
    "Not Sent": "default",
    "Awaiting Acceptance": "warning",
    "Waiting for Authorisation": "warning",
    "Waiting for Approval": "warning",
    "Waiting for HR": "warning",
    Pending: "warning",
    Authorised: "info",
    Accepted: "success",
    Active: "primary",
    Approved: "success",
    Paid: "success",
    Claimed: "success",
    Submitted: "success",
    "Handed Back": "default",
    Returned: "warning",
    Unpaid: "warning",
    "Partly Claimed and Returned": "info",
    Rejected: "error",
    Declined: "error",
    Cancelled: "default",
    Withdrawn: "default"
  },
  "default"
);
function $n(a) {
  switch (a) {
    case "Open":
      return e("Open");
    case "Draft":
      return e("Draft");
    case "Not Sent":
      return e("Not Sent");
    case "Awaiting Acceptance":
      return e("Awaiting Acceptance");
    case "Waiting for Authorisation":
      return e("Waiting for Authorisation");
    case "Waiting for Approval":
      return e("Waiting for Approval");
    case "Waiting for HR":
      return e("Waiting for HR");
    case "Pending":
      return e("Answer Needed");
    case "Authorised":
      return e("Authorised");
    case "Accepted":
      return e("Accepted");
    case "Active":
      return e("Active");
    case "Approved":
      return e("Approved");
    case "Paid":
      return e("Paid");
    case "Unpaid":
      return e("Unpaid");
    case "Claimed":
      return e("Claimed");
    case "Submitted":
      return e("Submitted");
    case "Handed Over":
      return e("Handed Over");
    case "Handed Back":
      return e("Handed Back");
    case "Done while away":
      return e("Done While Away");
    case "Already done":
      return e("Already Done");
    case "Returned":
      return e("Returned");
    case "Rejected":
      return e("Rejected");
    case "Declined":
      return e("Declined");
    case "Cancelled":
      return e("Cancelled");
    case "Withdrawn":
      return e("Withdrawn");
    default:
      return a ?? "";
  }
}
function T({ value: a }) {
  return a ? /* @__PURE__ */ t(an, { status: a, label: $n(a), toneOf: Wn }) : null;
}
const En = 864e5;
function Ot(a) {
  const [i, n, o] = a.split("-").map(Number);
  return Date.UTC(i, n - 1, o);
}
function qn(a) {
  return new Date(a).toISOString().slice(0, 10);
}
function pe(a, i) {
  return qn(Ot(a) + i * En);
}
function Ve(a) {
  const i = (new Date(Ot(a)).getUTCDay() + 6) % 7;
  return pe(a, -i);
}
function Y(a = /* @__PURE__ */ new Date()) {
  const i = (n) => String(n).padStart(2, "0");
  return `${a.getFullYear()}-${i(a.getMonth() + 1)}-${i(a.getDate())}`;
}
function Ie(a) {
  return Array.from({ length: 7 }, (i, n) => pe(a, n));
}
function ke(a) {
  const i = typeof a == "number" ? a : Number.parseFloat(String(a ?? ""));
  return Number.isFinite(i) && i > 0 ? Math.round(i * 100) / 100 : 0;
}
function zt(a, i) {
  return Math.round(a.reduce((n, o) => n + ke(o.hours[i]), 0) * 100) / 100;
}
function Tn(a) {
  return Math.round(Ie("2000-01-03").reduce((i, n, o) => i + zt(a, o), 0) * 100) / 100;
}
function et(a, i) {
  return { row: a.reduce((o, s) => Math.max(o, s.row), 0) + 1, activity_type: i, description: "", is_billable: 0, hours: [0, 0, 0, 0, 0, 0, 0] };
}
function Hn(a) {
  return a.map((i, n) => ({
    row: n + 1,
    activity_type: i.activity_type,
    project: i.project ?? null,
    task: i.task ?? null,
    description: i.description ?? "",
    is_billable: i.is_billable ? 1 : 0,
    hours: [0, 0, 0, 0, 0, 0, 0]
  }));
}
function Bn(a, i, n, o) {
  return a.map((s) => s.row === i ? { ...s, hours: s.hours.map((c, r) => ke(r === n ? o : c)) } : s);
}
function Pn(a) {
  return a.filter((i) => i.hours.some((n) => ke(n) > 0) || (i.description ?? "").trim()).map((i, n) => ({ ...i, row: n + 1, hours: Array.from({ length: 7 }, (o, s) => ke(i.hours[s])) }));
}
function Fn() {
  return "geolocation" in navigator ? new Promise(
    (a) => navigator.geolocation.getCurrentPosition(
      (i) => a({ latitude: i.coords.latitude, longitude: i.coords.longitude }),
      () => a(null),
      { enableHighAccuracy: !0, timeout: 1e4, maximumAge: 6e4 }
    )
  ) : Promise.resolve(null);
}
function In() {
  const a = D(), i = V(), { data: n, isLoading: o, error: s, mutate: c } = N(f.checkinStatus), r = q(f.checkIn), [u, p] = E(!1), [v, y] = E(!1), d = async () => {
    if (!n) return;
    y(!1);
    let h = null;
    n.location && (p(!0), h = await Fn(), p(!1), y(!h));
    try {
      await r.run({ log_type: n.next, ...h ?? {} }), i.success(n.next === "IN" ? e("Checked in.") : e("Checked out.")), await c();
    } catch {
    }
  };
  return /* @__PURE__ */ t(te, { title: e("Check-in"), onBack: () => a(""), loading: o, error: s, onRetry: c, children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
    n.offered ? /* @__PURE__ */ m(fe, { children: [
      r.errorMessage && /* @__PURE__ */ t($, { tone: "error", children: r.errorMessage }),
      v && /* @__PURE__ */ t($, { tone: "warning", children: e("Your phone did not share where you are. Allow location for this site if HR needs it.") }),
      /* @__PURE__ */ m(w, { size: "lg", loading: u || r.loading, onClick: d, children: [
        n.next === "IN" ? /* @__PURE__ */ t(Dn, {}) : /* @__PURE__ */ t(Sn, {}),
        n.next === "IN" ? e("Check In") : e("Check Out")
      ] }),
      n.location && /* @__PURE__ */ m(ee, { size: "sm", muted: !0, children: [
        /* @__PURE__ */ t(Ye, { "aria-hidden": !0, className: "mr-1 inline size-4" }),
        e("Where you are is recorded with each check-in, as HR asks.")
      ] })
    ] }) : /* @__PURE__ */ t($, { tone: "info", children: e("HR has not turned on checking in from the phone.") }),
    /* @__PURE__ */ t(F, { title: e("Today"), children: n.today.length === 0 ? /* @__PURE__ */ t(ee, { muted: !0, children: e("No check-ins today yet. Clock-ins on the office device show here too.") }) : /* @__PURE__ */ t(L, { divided: !0, children: n.today.map((h) => /* @__PURE__ */ t(
      M,
      {
        primary: h.log_type === "IN" ? e("In") : e("Out"),
        secondary: h.device_id ? e("{0} · {1}", [xe(h.time), h.device_id]) : xe(h.time)
      },
      h.name
    )) }) })
  ] }) });
}
function On() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.attendanceRequests);
  return /* @__PURE__ */ t(
    ne,
    {
      title: e("Attendance Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.attendanceNew), children: [
        /* @__PURE__ */ t(me, {}),
        e("New Request")
      ] }),
      children: c && !i?.attendance.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Ye, {}), title: e("No attendance requests"), description: e("Ask for days you worked from home or on duty elsewhere to count as attended.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i?.attendance ?? []).map((r) => /* @__PURE__ */ t(
        M,
        {
          primary: r.reason === "Work From Home" ? e("Work From Home") : e("On Duty"),
          secondary: e("{0} to {1}", [g(r.from_date), g(r.to_date)]),
          action: /* @__PURE__ */ t(T, { value: r.docstatus === 1 ? "Approved" : r.docstatus === 2 ? "Cancelled" : "Open" }),
          onClick: () => a(l.attendanceRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function zn() {
  const a = D(), i = V(), n = q(f.requestAttendance), o = ce(() => le.object({ from_date: _e(() => e("From Date")), to_date: _e(() => e("To Date")), reason: we(() => e("Reason")) }).loose(), []), s = de({
    schema: o,
    defaultValues: { from_date: Y(), to_date: Y(), reason: "Work From Home", explanation: "", half_day: !1 }
  }), c = s.watch("from_date");
  return /* @__PURE__ */ t(te, { title: e("New Attendance Request"), onBack: () => a(l.attendance), children: /* @__PURE__ */ m(
    ue,
    {
      form: s,
      onSubmit: async (r) => {
        const u = await n.run({ ...r, half_day: r.half_day ? 1 : 0 });
        i.success(e("Request sent to HR.")), a(l.attendanceRecord(u));
      },
      children: [
        /* @__PURE__ */ t(
          lt,
          {
            name: "reason",
            label: e("Reason"),
            required: !0,
            options: [
              { value: "Work From Home", label: e("Work From Home") },
              { value: "On Duty", label: e("On Duty"), description: e("Working away from the office, e.g. a field visit.") }
            ]
          }
        ),
        /* @__PURE__ */ t(re, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(re, { name: "to_date", label: e("To Date"), required: !0, minDate: c || void 0 }),
        /* @__PURE__ */ t(ct, { name: "half_day", label: e("Half Day") }),
        /* @__PURE__ */ t(U, { name: "explanation", label: e("Explanation"), multiline: !0, rows: 3 }),
        /* @__PURE__ */ t(he, { submitLabel: e("Send Request"), onCancel: () => a(l.attendance) })
      ]
    }
  ) });
}
function tt({ doctype: a }) {
  const i = D(), n = oe(Z().name), { data: o, isLoading: s, error: c, mutate: r } = N(f.attendanceRecord, { doctype: a, name: n }), u = a === "Shift Request";
  return /* @__PURE__ */ t(
    Q,
    {
      title: u ? e("Shift Request") : e("Attendance Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t(T, { value: u ? o.status : o.docstatus === 1 ? "Approved" : "Open" }),
      onBack: () => i(u ? l.shifts : l.attendance),
      loading: s,
      error: c,
      onRetry: r,
      children: o && /* @__PURE__ */ t(
        J,
        {
          items: [
            { label: e("Shift Type"), value: o.shift_type ?? null, hideWhenEmpty: !0 },
            { label: e("Reason"), value: o.reason ?? null, hideWhenEmpty: !0 },
            { label: e("From Date"), value: g(o.from_date) },
            { label: e("To Date"), value: o.to_date ? g(o.to_date) : null, hideWhenEmpty: !0 },
            { label: e("Approver"), value: o.approver_name, hideWhenEmpty: !0 },
            { label: e("Explanation"), value: o.explanation ?? null, hideWhenEmpty: !0, full: !0 }
          ]
        }
      )
    }
  );
}
function jn() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.attendanceRequests);
  return /* @__PURE__ */ t(
    ne,
    {
      title: e("Shift Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.shiftNew), children: [
        /* @__PURE__ */ t(me, {}),
        e("New Request")
      ] }),
      children: c && !i?.shifts.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Tt, {}), title: e("No shift requests"), description: e("Ask to work a different shift for some days.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i?.shifts ?? []).map((r) => /* @__PURE__ */ t(
        M,
        {
          primary: r.shift_type,
          secondary: r.to_date ? e("{0} to {1}", [g(r.from_date), g(r.to_date)]) : e("From {0}", [g(r.from_date)]),
          action: /* @__PURE__ */ t(T, { value: r.status }),
          onClick: () => a(l.shiftRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function Yn() {
  const a = D(), i = V(), n = N(f.attendanceOptions), o = q(f.requestShift), s = ce(() => le.object({ shift_type: we(() => e("Shift Type")), from_date: _e(() => e("From Date")) }).loose(), []), c = de({ schema: s, defaultValues: { shift_type: "", from_date: Y(), to_date: "" } });
  return /* @__PURE__ */ m(te, { title: e("New Shift Request"), onBack: () => a(l.shifts), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    n.data && !n.data.has_shift_approver && /* @__PURE__ */ t($, { tone: "warning", children: e("Nobody approves your shift requests yet. Ask HR to set a shift approver.") }),
    /* @__PURE__ */ m(
      ue,
      {
        form: c,
        onSubmit: async (r) => {
          const u = await o.run({ shift_type: r.shift_type, from_date: r.from_date, to_date: r.to_date || void 0 });
          i.success(e("Request sent to {0}.", [n.data?.shift_approver_name ?? e("your shift approver")])), a(l.shiftRecord(u));
        },
        children: [
          /* @__PURE__ */ t(Ae, { name: "shift_type", label: e("Shift Type"), required: !0, options: (n.data?.shift_types ?? []).map((r) => ({ value: r, label: r })) }),
          /* @__PURE__ */ t(re, { name: "from_date", label: e("From Date"), required: !0 }),
          /* @__PURE__ */ t(re, { name: "to_date", label: e("To Date"), hint: e("Leave empty if the shift carries on.") }),
          /* @__PURE__ */ t(he, { submitLabel: e("Send Request"), onCancel: () => a(l.shifts) })
        ]
      }
    )
  ] });
}
function We(a, i, n) {
  return /* @__PURE__ */ t(L, { divided: !0, children: a.map((o) => /* @__PURE__ */ t(
    M,
    {
      primary: i ? e("Covered by {0}", [o.stand_in]) : o.employee_name,
      secondary: e("{0} to {1}", [g(o.leave_from), g(o.leave_to)]),
      action: /* @__PURE__ */ t(T, { value: o.waiting_for_me ? "Pending" : o.status }),
      onClick: () => n(l.handover(o.name))
    },
    o.name
  )) });
}
function Vn() {
  const a = D(), [i, n] = E("to_answer"), { data: o, isLoading: s, error: c, mutate: r, hasLoaded: u } = N(f.cover), p = (v, y) => /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Pt, {}), title: v, description: y });
  return /* @__PURE__ */ m(ne, { title: e("Cover"), onBack: () => a(""), loading: s, error: c, onRetry: r, children: [
    /* @__PURE__ */ t(
      on,
      {
        label: e("Handovers"),
        value: i,
        onChange: n,
        items: [
          { id: "to_answer", label: e("To Answer"), count: o?.to_answer.filter((v) => v.waiting_for_me).length },
          { id: "covering", label: e("Covering"), count: o?.covering.length },
          { id: "mine", label: e("Mine"), count: o?.mine.length }
        ]
      }
    ),
    /* @__PURE__ */ t(Se, { id: "to_answer", value: i, children: u && !o?.to_answer.length ? p(e("Nobody has asked you to cover"), e("When a colleague names you as their stand-in, it shows here for you to agree or decline.")) : We(o?.to_answer ?? [], !1, a) }),
    /* @__PURE__ */ t(Se, { id: "covering", value: i, children: u && !o?.covering.length ? p(e("You are not covering anyone now"), e("Work you agreed to cover shows here while the person is away.")) : We(o?.covering ?? [], !1, a) }),
    /* @__PURE__ */ t(Se, { id: "mine", value: i, children: u && !o?.mine.length ? p(e("No handovers of your own"), e("When you apply for leave, the handover you send shows here.")) : We(o?.mine ?? [], !0, a) })
  ] });
}
function Un() {
  const a = D(), i = V(), n = oe(Z().name), { data: o, isLoading: s, error: c, mutate: r } = N(f.handoverRecord, { name: n }), u = q(f.respond), p = q(f.respondAuthority), v = q(f.addNote), y = q(f.returnNote), d = q(f.returnWork), [h, R] = E(null), [x, W] = E(""), [S, A] = E(!1), [P, j] = E(!1), [I, G] = E(null), O = async (k, Ne) => {
    j(!0), G(null);
    try {
      await k(), i.success(Ne), R(null), W(""), await r();
    } catch (ie) {
      G(ie);
    } finally {
      j(!1);
    }
  }, _ = o && o.can_answer ? /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(w, { variant: "outline", onClick: () => R({ kind: "decline" }), children: e("Decline") }),
    /* @__PURE__ */ t(w, { loading: P, onClick: () => O(() => u.run({ name: n, answer: "Accepted" }), e("You agreed to cover this.")), children: e("Accept") })
  ] }) : o && o.can_return ? /* @__PURE__ */ t(w, { onClick: () => A(!0), children: e("I'm Back") }) : void 0;
  return /* @__PURE__ */ m(
    Q,
    {
      title: o ? o.is_owner ? e("My Handover") : e("Cover for {0}", [o.employee_name]) : e("Handover"),
      subtitle: o && e("{0} to {1}", [g(o.leave_from), g(o.leave_to)]),
      meta: o && /* @__PURE__ */ t(T, { value: o.status }),
      onBack: () => a(l.cover),
      actions: _,
      loading: s,
      error: c,
      onRetry: r,
      children: [
        o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
          I ? /* @__PURE__ */ t($, { tone: "error", children: u.errorMessage || p.errorMessage || d.errorMessage || e("That did not go through. Try again.") }) : null,
          /* @__PURE__ */ t(
            J,
            {
              items: [
                { label: e("Stand-in"), value: o.stand_in },
                { label: e("Back On"), value: o.return_date ? g(o.return_date) : null, hideWhenEmpty: !0 },
                { label: e("Decline Reason"), value: o.decline_reason, hideWhenEmpty: !0, full: !0 },
                { label: e("Handover Notes"), value: o.notes, hideWhenEmpty: !0, full: !0 },
                { label: e("Return Note"), value: o.return_note, hideWhenEmpty: !0, full: !0 }
              ]
            }
          ),
          /* @__PURE__ */ t(F, { title: e("Work"), children: o.work.length === 0 ? /* @__PURE__ */ t(ee, { muted: !0, children: e("No work items were handed over; the notes say what to look after.") }) : /* @__PURE__ */ t(L, { divided: !0, children: o.work.map((k) => /* @__PURE__ */ t(
            M,
            {
              primary: k.description,
              secondary: [k.covered_by, k.due_date ? e("Due {0}", [g(k.due_date)]) : "", k.notes ?? ""].filter(Boolean).join(" · "),
              action: k.mine && o.status === "Active" ? /* @__PURE__ */ t(w, { variant: "ghost", onClick: () => R({ kind: "note", row: k.row, text: k.notes ?? "" }), children: e("Leave a Note") }) : k.progress || k.acceptance ? /* @__PURE__ */ t(T, { value: k.progress || k.acceptance }) : void 0
            },
            k.row
          )) }) }),
          o.approvals.length > 0 && /* @__PURE__ */ t(F, { title: e("Approvals"), children: /* @__PURE__ */ t(L, { divided: !0, children: o.approvals.map((k) => /* @__PURE__ */ t(
            M,
            {
              primary: k.label,
              secondary: k.covered_by,
              action: k.mine && o.can_answer && k.acceptance === "Pending" ? /* @__PURE__ */ m("div", { className: "flex gap-1", children: [
                /* @__PURE__ */ t(w, { variant: "ghost", onClick: () => R({ kind: "decline-approval", row: k.row }), children: e("Decline") }),
                /* @__PURE__ */ t(
                  w,
                  {
                    variant: "ghost",
                    onClick: () => O(() => p.run({ name: n, row: k.row, answer: "Accepted" }), e("You agreed to approve in their place.")),
                    children: e("Accept")
                  }
                )
              ] }) : k.acceptance ? /* @__PURE__ */ t(T, { value: k.acceptance }) : void 0
            },
            k.row
          )) }) }),
          o.is_stand_in && o.status === "Active" && /* @__PURE__ */ t(w, { variant: "outline", onClick: () => R({ kind: "return-note" }), children: e("Note for Return") })
        ] }),
        /* @__PURE__ */ t(
          mt,
          {
            open: !!h,
            onClose: () => R(null),
            title: h?.kind === "note" ? e("Leave a Note") : h?.kind === "return-note" ? e("Note for Return") : e("Decline"),
            description: h?.kind === "note" ? e("What you did on this piece of work, for when they are back.") : h?.kind === "return-note" ? e("What they should know on their first day back.") : e("Say why you cannot cover it, so they can ask someone else."),
            actions: /* @__PURE__ */ m(fe, { children: [
              /* @__PURE__ */ t(w, { variant: "outline", onClick: () => R(null), children: e("Cancel") }),
              /* @__PURE__ */ t(
                w,
                {
                  loading: P,
                  disabled: !(h?.kind === "note" ? h.text : x).trim(),
                  onClick: () => {
                    h && (h.kind === "decline" ? O(() => u.run({ name: n, answer: "Declined", reason: x }), e("You declined.")) : h.kind === "decline-approval" ? O(() => p.run({ name: n, row: h.row, answer: "Declined", reason: x }), e("You declined.")) : h.kind === "note" ? O(() => v.run({ name: n, row: h.row, note: h.text }), e("Note saved.")) : O(() => y.run({ name: n, note: x }), e("Note saved.")));
                  },
                  children: h?.kind === "decline" || h?.kind === "decline-approval" ? e("Decline") : e("Save Note")
                }
              )
            ] }),
            children: /* @__PURE__ */ t(
              rn,
              {
                "aria-label": e("Note"),
                rows: 4,
                value: h?.kind === "note" ? h.text : x,
                onChange: (k) => h?.kind === "note" ? R({ ...h, text: k.target.value }) : W(k.target.value)
              }
            )
          }
        ),
        /* @__PURE__ */ t(
          pt,
          {
            open: S,
            onClose: () => A(!1),
            title: e("Take your work back now?"),
            confirmLabel: e("I'm Back"),
            onConfirm: async () => {
              await d.run({ name: n }), i.success(e("Your work is back with you.")), await r();
            },
            children: e("Everything your stand-in was covering comes back to you, and they stop approving in your place.")
          }
        )
      ]
    }
  );
}
function Jn() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s } = N(f.home), c = l.week(Ve(Y())), r = [
    { label: e("Leave"), hint: e("Apply, and see what you asked for"), path: l.leave, icon: /* @__PURE__ */ t(He, {}) },
    { label: e("Cover"), hint: e("Handovers to answer and work you cover"), path: l.cover, icon: /* @__PURE__ */ t(Pt, {}) },
    { label: e("Time Off in Lieu"), hint: e("Claim extra hours as time off"), path: l.toil, icon: /* @__PURE__ */ t(Pe, {}) },
    { label: e("Timesheets"), hint: e("Your week, day by day"), path: l.timesheet, icon: /* @__PURE__ */ t(Be, {}) },
    { label: e("Expense Claims"), hint: e("Claims and receipts"), path: l.expenses, icon: /* @__PURE__ */ t(Fe, {}) },
    { label: e("Advances"), hint: e("Money paid ahead and what is left to settle"), path: l.advances, icon: /* @__PURE__ */ t(Nt, {}) },
    { label: e("Payslips"), hint: e("Your pay, month by month"), path: l.pay, icon: /* @__PURE__ */ t(It, {}) },
    { label: e("Attendance Requests"), hint: e("Days worked away from the office"), path: l.attendance, icon: /* @__PURE__ */ t(Ye, {}) },
    { label: e("Shift Requests"), hint: e("Ask to work another shift"), path: l.shifts, icon: /* @__PURE__ */ t(Tt, {}) },
    { label: e("My Details"), hint: e("Contact, dependants and where you are paid"), path: l.me, icon: /* @__PURE__ */ t(Nn, {}) }
  ];
  return i?.checkin.offered && r.splice(4, 0, { label: e("Check-in"), hint: e("Check in and out from your phone"), path: l.checkIn, icon: /* @__PURE__ */ t(Qe, {}) }), /* @__PURE__ */ t(sn, { title: e("My HR"), subtitle: i?.employee.employee_name, loading: n, error: o, onRetry: s, children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
    i && i.balances.length > 0 && /* @__PURE__ */ t(yt, { columns: 2, children: i.balances.map((u) => /* @__PURE__ */ t(Ee, { label: u.label, value: e("{0} days", [String(u.value)]), onClick: () => a(u.key.startsWith("toil") ? l.toil : l.leave) }, u.key)) }),
    /* @__PURE__ */ t(F, { title: e("Quick Actions"), children: /* @__PURE__ */ m("div", { className: "grid grid-cols-1 gap-2 sm:grid-cols-2", children: [
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.leaveNew), children: [
        /* @__PURE__ */ t(He, {}),
        e("Apply for Leave")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.toilNew), children: [
        /* @__PURE__ */ t(Pe, {}),
        e("Claim Time Off")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(c), children: [
        /* @__PURE__ */ t(An, {}),
        e("This Week's Timesheet")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.expenseNew), children: [
        /* @__PURE__ */ t(Fe, {}),
        e("New Expense Claim")
      ] }),
      i?.checkin.offered && /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.checkIn), children: [
        /* @__PURE__ */ t(Qe, {}),
        e("Check In")
      ] })
    ] }) }),
    i && i.in_flight.length > 0 && /* @__PURE__ */ t(F, { title: e("In Progress"), children: /* @__PURE__ */ t(L, { divided: !0, children: i.in_flight.map((u) => {
      const p = hn(u.doctype);
      return /* @__PURE__ */ t(M, { primary: u.label, action: /* @__PURE__ */ t(ge, { children: u.count }), onClick: p ? () => a(p) : void 0 }, u.key);
    }) }) }),
    /* @__PURE__ */ t(F, { title: e("Everything in My HR"), children: /* @__PURE__ */ t(L, { divided: !0, children: r.map((u) => /* @__PURE__ */ t(M, { primary: u.label, secondary: u.hint, icon: u.icon, action: /* @__PURE__ */ t(kt, { "aria-hidden": !0 }), onClick: () => a(u.path) }, u.path)) }) })
  ] }) });
}
const Gn = "seal-draft:", Kn = 30, Xn = 400;
function Zn(a, i, n) {
  return `${Gn}${a}:${i}:${n}`;
}
function Ue() {
  try {
    return typeof window < "u" ? window.localStorage : null;
  } catch {
    return null;
  }
}
function Oe(a, i = Date.now()) {
  const n = Ue();
  if (!n) return null;
  try {
    const o = n.getItem(a);
    if (!o) return null;
    const s = JSON.parse(o);
    if (!s || typeof s.saved != "number" || !("value" in s)) throw new Error("not a draft");
    return i - s.saved > Kn * 864e5 ? (n.removeItem(a), null) : { value: s.value, saved: s.saved };
  } catch {
    try {
      n.removeItem(a);
    } catch {
    }
    return null;
  }
}
function Qn(a, i, n = Date.now()) {
  const o = Ue();
  if (!o) return !1;
  try {
    return o.setItem(a, JSON.stringify({ saved: n, value: i })), !0;
  } catch {
    return !1;
  }
}
function jt(a) {
  try {
    Ue()?.removeItem(a);
  } catch {
  }
}
function Je(a, i, n) {
  const o = a && n ? Zn(a, i, n) : null, [s, c] = E(() => o ? Oe(o) : null), r = Re(null), u = Re(o);
  ye(() => {
    u.current !== o && (u.current = o, c(o ? Oe(o) : null));
  }, [o]), ye(
    () => () => {
      r.current && clearTimeout(r.current);
    },
    []
  );
  const p = be(
    (d) => {
      o && (r.current && clearTimeout(r.current), r.current = setTimeout(() => Qn(o, d), Xn));
    },
    [o]
  ), v = be(() => {
    r.current && clearTimeout(r.current), r.current = null, o && jt(o), c(null);
  }, [o]), y = be(() => c(null), []);
  return { key: o, restored: s, keep: p, clear: v, dismiss: y };
}
function Ge(a) {
  return Y(new Date(a));
}
function ea(a) {
  return { show: !!a?.needed, standInRequired: !!a?.needed && !!a?.required };
}
function ta(a, i) {
  const n = a.filter((c) => c.work_date), o = new Set(n.map((c) => c.work_date)), s = i.filter((c) => !o.has(c.work_date)).map((c) => ({ work_date: c.work_date, hours: c.hours, work_done: "" }));
  return [...n, ...s].sort((c, r) => c.work_date.localeCompare(r.work_date));
}
function na(a) {
  if (a.change === "Mobile Money") return a.mobile_no?.trim() ? [] : ["mobile_no"];
  const i = ["bank", "bank_account_no", "account_name"].filter((n) => !a[n]?.trim());
  return a.evidence ? i : [...i, "evidence"];
}
function aa() {
  const a = D(), [i, n] = E("all"), { data: o, isLoading: s, error: c, mutate: r, hasLoaded: u } = N(f.leaveList), p = o ?? [], v = p.filter((d) => d.status === "Open" && d.docstatus === 0), y = i === "open" ? v : i === "decided" ? p.filter((d) => !v.includes(d)) : p;
  return /* @__PURE__ */ t(
    ne,
    {
      title: e("Leave"),
      onBack: () => a(""),
      loading: s,
      error: c,
      onRetry: r,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.leaveNew), children: [
        /* @__PURE__ */ t(me, {}),
        e("Apply for Leave")
      ] }),
      toolbar: /* @__PURE__ */ t(
        ln,
        {
          label: e("Show"),
          value: i,
          onChange: n,
          options: [
            { value: "all", label: e("All"), count: p.length },
            { value: "open", label: e("Waiting"), count: v.length },
            { value: "decided", label: e("Decided"), count: p.length - v.length }
          ]
        }
      ),
      children: u && y.length === 0 ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(He, {}), title: e("No leave here"), description: e("Leave you apply for shows here until it is decided, and after.") }) : /* @__PURE__ */ t(L, { divided: !0, children: y.map((d) => /* @__PURE__ */ t(
        M,
        {
          primary: d.leave_type,
          secondary: d.handover ? e("{0} to {1} · {2} days · covered by {3}", [g(d.from_date), g(d.to_date), String(d.total_leave_days), d.handover.stand_in]) : e("{0} to {1} · {2} days", [g(d.from_date), g(d.to_date), String(d.total_leave_days)]),
          action: /* @__PURE__ */ t(T, { value: d.status }),
          onClick: () => a(l.leaveRecord(d.name))
        },
        d.name
      )) })
    }
  );
}
function oa() {
  const a = D(), i = V(), [n] = rt(), o = ce(
    () => le.object({
      leave_type: we(() => e("Leave Type")),
      from_date: _e(() => e("From Date")),
      to_date: _e(() => e("To Date"))
    }),
    []
  ), s = () => ({ leave_type: n.get("type") ?? "", from_date: "", to_date: "", half_day: !1, description: "", stand_in: "", handover_notes: "", todos: [], approvals: [] }), c = de({ schema: o.passthrough(), defaultValues: s() }), r = Je(ve().user, "leave-application", "new"), [u, p] = E(null);
  ye(() => {
    r.restored?.value && !n.get("type") && (c.reset({ ...s(), ...r.restored.value }), p(r.restored.saved)), r.dismiss();
    const _ = c.watch((k) => r.keep({ ...s(), ...k }));
    return () => _.unsubscribe();
  }, []);
  const v = () => {
    r.clear(), p(null), c.reset(s());
  }, [y, d, h, R] = c.watch(["leave_type", "from_date", "to_date", "half_day"]), x = !!(y && d && h), W = N(f.leaveOptions), S = N(f.leaveOptions, { leave_type: y, from_date: d, to_date: h, half_day: R ? 1 : 0 }, { enabled: x }), A = { ...S, data: x ? S.data : void 0 }, P = N(f.colleagues, {}, { enabled: !!A.data?.handover.needed }), j = q(f.applyForLeave), I = ea(x ? A.data?.handover : void 0), G = (A.data ?? W.data)?.leave_types.find((_) => _.name === y), O = async (_) => {
    if (I.standInRequired && !_.stand_in) return { errors: { stand_in: e("Your company asks for cover on this leave. Choose who will cover your work.") } };
    const k = await j.run({
      leave_type: _.leave_type,
      from_date: _.from_date,
      to_date: _.to_date,
      half_day: _.half_day ? 1 : 0,
      description: _.description,
      stand_in: I.show && _.stand_in || void 0,
      handover_notes: _.handover_notes,
      todos: JSON.stringify(_.todos),
      approvals: JSON.stringify(_.approvals)
    });
    r.clear(), i.success(k.handover ? e("Leave applied for, and the handover sent to your stand-in.") : e("Leave applied for.")), a(l.leaveRecord(k.name));
  };
  return /* @__PURE__ */ m(te, { title: e("Apply for Leave"), onBack: () => a(l.leave), loading: W.isLoading && !W.data, error: W.error, onRetry: W.mutate, children: [
    u !== null && /* @__PURE__ */ t($, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: v, children: e("Start Again") }), children: e("You started this application on {0} and had not sent it.", [g(Ge(u))]) }),
    /* @__PURE__ */ m(ue, { form: c, onSubmit: O, children: [
      /* @__PURE__ */ t(Ze, { title: e("Leave"), children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          Ae,
          {
            name: "leave_type",
            label: e("Leave Type"),
            required: !0,
            options: (W.data?.leave_types ?? []).map((_) => ({
              value: _.name,
              label: _.name,
              description: _.left === null ? e("Unpaid") : e("{0} days left", [String(_.left)])
            })),
            hint: G && G.left !== null ? e("{0} days left", [String(G.left)]) : void 0
          }
        ),
        /* @__PURE__ */ t(re, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(re, { name: "to_date", label: e("To Date"), required: !0, minDate: d || void 0 }),
        /* @__PURE__ */ t(ct, { name: "half_day", label: e("Half Day"), hint: e("Only the first day is a half day.") }),
        /* @__PURE__ */ t(U, { name: "description", label: e("Reason"), multiline: !0, rows: 3 }),
        x && A.data && /* @__PURE__ */ t($, { tone: "info", children: A.data.days !== null ? e("{0} days, approved by {1}.", [String(A.data.days), A.data.approver_name ?? e("your leave approver")]) : e("Approved by {0}.", [A.data.approver_name ?? e("your leave approver")]) })
      ] }) }),
      I.show && /* @__PURE__ */ t(
        Ze,
        {
          title: e("Handover"),
          description: I.standInRequired ? e("Your company asks for cover on leave like this. Your stand-in is asked to agree before the leave is approved.") : e("Your company suggests arranging cover. You can leave this out."),
          children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
            /* @__PURE__ */ t(
              De,
              {
                name: "stand_in",
                label: e("Stand-in"),
                required: I.standInRequired,
                options: (P.data ?? []).map((_) => ({ value: _.name, label: _.employee_name })),
                hint: e("A colleague in your company who is not away at the same time.")
              }
            ),
            /* @__PURE__ */ t(U, { name: "handover_notes", label: e("Handover Notes"), multiline: !0, rows: 4, hint: e("What your stand-in needs to know.") }),
            (A.data?.work.length ?? 0) > 0 && /* @__PURE__ */ t(
              De,
              {
                name: "todos",
                multiple: !0,
                label: e("Work to Hand Over"),
                options: (A.data?.work ?? []).map((_) => ({ value: _.todo, label: _.description, description: _.due_date ? e("Due {0}", [g(_.due_date)]) : void 0 })),
                hint: e("Open items on your work list. Your stand-in gets them while you are away.")
              }
            ),
            (A.data?.approvals.length ?? 0) > 0 && /* @__PURE__ */ t(
              De,
              {
                name: "approvals",
                multiple: !0,
                label: e("Approvals to Hand Over"),
                options: (A.data?.approvals ?? []).map((_) => ({ value: _.authority, label: _.authority_label })),
                hint: e("Your stand-in approves these in your place, once they agree.")
              }
            )
          ] })
        }
      ),
      /* @__PURE__ */ t(he, { submitLabel: e("Apply"), onCancel: () => a(l.leave) })
    ] })
  ] });
}
function ia() {
  const a = D(), i = oe(Z().name), { data: n, isLoading: o, error: s, mutate: c } = N(f.leaveRecord, { name: i });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n ? n.leave_type : e("Leave"),
      subtitle: n && !n.mine ? n.employee_name : i,
      meta: n && /* @__PURE__ */ t(T, { value: n.status }),
      onBack: () => a(l.leave),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          J,
          {
            items: [
              { label: e("From Date"), value: g(n.from_date) },
              { label: e("To Date"), value: g(n.to_date) },
              { label: e("Days"), value: String(n.total_leave_days) },
              { label: e("Half Day"), value: n.half_day ? e("Yes") : e("No") },
              { label: e("Leave Approver"), value: n.leave_approver_name, hideWhenEmpty: !0 },
              { label: e("Applied On"), value: g(n.posting_date) },
              { label: e("Reason"), value: n.description, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        n.handover ? /* @__PURE__ */ t(L, { divided: !0, children: /* @__PURE__ */ t(
          M,
          {
            primary: e("Handover to {0}", [n.handover.stand_in]),
            action: /* @__PURE__ */ t(T, { value: n.handover.status }),
            onClick: () => a(l.handover(n.handover.name))
          }
        ) }) : /* @__PURE__ */ t(ee, { muted: !0, children: e("No handover for this leave.") })
      ] })
    }
  );
}
class Yt extends Error {
  constructor() {
    super(...arguments);
    Xe(this, "name", "VerificationCancelled");
  }
}
function ze(a, i = 0) {
  if (!a || typeof a != "object" || i > 3) return !1;
  const n = a;
  return n.exc_type === "VerificationNeeded" || typeof n.exception == "string" && n.exception.includes("VerificationNeeded") ? !0 : ze(n.payload, i + 1) || ze(n.original, i + 1);
}
async function Vt(a, i) {
  try {
    return await a();
  } catch (n) {
    if (!ze(n)) throw n;
    if (!await i()) throw new Yt();
    return a();
  }
}
function ra() {
  const a = D(), i = V(), { data: n, isLoading: o, error: s, mutate: c } = N(f.myDetails), r = q(f.updateMyContact), [u, p] = E(!1), [v, y] = E("");
  return /* @__PURE__ */ m(Q, { title: e("My Details"), subtitle: n?.employee.employee_name, onBack: () => a(""), loading: o, error: s, onRetry: c, children: [
    n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
      /* @__PURE__ */ t(
        J,
        {
          items: [
            { label: e("Employee ID"), value: n.employee.name },
            { label: e("Designation"), value: n.employee.designation, hideWhenEmpty: !0 },
            { label: e("Department"), value: n.employee.department, hideWhenEmpty: !0 },
            { label: e("Company"), value: n.employee.company },
            { label: e("Date of Joining"), value: n.employee.date_of_joining ? g(n.employee.date_of_joining) : null, hideWhenEmpty: !0 },
            { label: e("Company Email"), value: n.employee.company_email, hideWhenEmpty: !0 },
            { label: e("Personal Email"), value: n.employee.personal_email, hideWhenEmpty: !0 }
          ]
        }
      ),
      /* @__PURE__ */ m(
        F,
        {
          title: e("Contact"),
          action: n.has_contact ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => p(!0), children: e("Change Mobile Number") }) : void 0,
          children: [
            /* @__PURE__ */ t(J, { items: [{ label: e("Mobile No."), value: n.mobile_no ?? e("None yet") }] }),
            !n.has_contact && /* @__PURE__ */ t(ee, { muted: !0, children: e("HR has not linked a contact to your record yet; ask them to.") })
          ]
        }
      ),
      /* @__PURE__ */ t(F, { title: e("Dependants and Beneficiaries"), children: n.dependants.length === 0 ? /* @__PURE__ */ t(ee, { muted: !0, children: e("None recorded. HR records dependants and beneficiaries.") }) : /* @__PURE__ */ t(L, { divided: !0, children: n.dependants.map((d) => /* @__PURE__ */ t(M, { primary: d.full_name, secondary: [d.relationship, d.type, d.dob ? g(d.dob) : ""].filter(Boolean).join(" · ") }, d.name)) }) }),
      /* @__PURE__ */ m(
        F,
        {
          title: e("Payout Details"),
          subtitle: e("Where your pay goes. Only the last four digits are shown."),
          action: /* @__PURE__ */ t(w, { disabled: !!n.payout_request, onClick: () => a(l.payoutNew), children: e("Request a Change") }),
          children: [
            /* @__PURE__ */ t(
              J,
              {
                items: [
                  { label: e("Bank"), value: n.payout.bank ?? e("None") },
                  { label: e("Account No."), value: n.payout.account_no, hideWhenEmpty: !0 },
                  { label: e("Account Name"), value: n.payout.account_name, hideWhenEmpty: !0 },
                  { label: e("Mobile Money"), value: n.payout.mobile_no ?? e("None") }
                ]
              }
            ),
            n.payout_requests.length > 0 && /* @__PURE__ */ t(L, { divided: !0, children: n.payout_requests.map((d) => /* @__PURE__ */ t(
              M,
              {
                primary: d.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
                secondary: xe(d.creation),
                action: /* @__PURE__ */ t(T, { value: d.status }),
                onClick: () => a(l.payoutRecord(d.name))
              },
              d.name
            )) })
          ]
        }
      )
    ] }),
    /* @__PURE__ */ t(
      mt,
      {
        open: u,
        onClose: () => p(!1),
        title: e("Change Mobile Number"),
        description: e("Your contact number at work. Where your pay goes changes only by a request to HR."),
        actions: /* @__PURE__ */ m(fe, { children: [
          /* @__PURE__ */ t(w, { variant: "outline", onClick: () => p(!1), children: e("Cancel") }),
          /* @__PURE__ */ t(
            w,
            {
              loading: r.loading,
              disabled: !v.trim(),
              onClick: async () => {
                try {
                  await r.run({ mobile_no: v }), i.success(e("Mobile number changed.")), p(!1), y(""), await c();
                } catch {
                }
              },
              children: e("Save")
            }
          )
        ] }),
        children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-2", children: [
          r.errorMessage && /* @__PURE__ */ t($, { tone: "error", children: r.errorMessage }),
          /* @__PURE__ */ t(Ce, { htmlFor: "new-mobile", children: e("New Mobile No.") }),
          /* @__PURE__ */ t(qe, { id: "new-mobile", type: "tel", inputMode: "tel", autoComplete: "tel", value: v, onChange: (d) => y(d.target.value) })
        ] })
      }
    )
  ] });
}
function sa() {
  const a = D(), i = ve(), n = V(), o = N(f.payoutOptions), s = q(f.requestPayoutChange), c = q(f.setPayoutEvidence), r = q(f.sendPayoutChange), u = de({
    defaultValues: { change: "Bank Account", bank: "", bank_account_no: "", branch_code: "", account_name: "", mobile_no: "", evidence: null, reason: "" }
  }), p = u.watch("change"), v = ce(
    () => ({ bank: e("Bank"), bank_account_no: e("Account No."), account_name: e("Account Name"), mobile_no: e("Mobile No."), evidence: e("Evidence") }),
    []
  ), y = async (d) => {
    const h = na(d);
    if (h.length) return { errors: Object.fromEntries(h.map((x) => [x, e("{0} is needed.", [v[x]])])) };
    const R = await s.run({
      change: d.change,
      bank: d.change === "Bank Account" ? d.bank : void 0,
      bank_account_no: d.change === "Bank Account" ? d.bank_account_no : void 0,
      branch_code: d.change === "Bank Account" ? d.branch_code : void 0,
      account_name: d.change === "Bank Account" ? d.account_name : void 0,
      mobile_no: d.change === "Mobile Money" ? d.mobile_no : void 0,
      reason: d.reason
    });
    if (d.change === "Bank Account" && d.evidence) {
      const x = await st(d.evidence, { doctype: "Payout Change Request", docname: R, fieldname: "evidence", isPrivate: !0 });
      await c.run({ name: R, file_url: x.file_url });
    }
    try {
      await Vt(() => r.run({ name: R }), i.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it."));
    } catch (x) {
      if (!(x instanceof Yt)) throw x;
      n.info(e("Saved, not sent. Open it from My Details to send it."));
    }
    a(l.payoutRecord(R));
  };
  return /* @__PURE__ */ m(te, { title: e("Request a Change"), subtitle: e("Where your pay goes"), onBack: () => a(l.me), loading: o.isLoading, error: o.error, onRetry: o.mutate, children: [
    /* @__PURE__ */ t($, { tone: "info", children: e("HR confirms every change before any pay goes there. We also tell your current number and email, in case this was not you.") }),
    /* @__PURE__ */ m(ue, { form: u, onSubmit: y, children: [
      /* @__PURE__ */ t(
        lt,
        {
          name: "change",
          label: e("Change"),
          required: !0,
          row: !0,
          options: [
            { value: "Bank Account", label: e("Bank Account") },
            { value: "Mobile Money", label: e("Mobile Money") }
          ]
        }
      ),
      p === "Bank Account" ? /* @__PURE__ */ m(fe, { children: [
        /* @__PURE__ */ t(Ae, { name: "bank", label: e("Bank"), required: !0, options: (o.data?.banks ?? []).map((d) => ({ value: d, label: d })) }),
        /* @__PURE__ */ t(U, { name: "bank_account_no", label: e("Account No."), required: !0 }),
        /* @__PURE__ */ t(U, { name: "branch_code", label: e("Branch") }),
        /* @__PURE__ */ t(U, { name: "account_name", label: e("Account Name"), required: !0, hint: e("As the bank has it. It must be in your own name.") }),
        /* @__PURE__ */ t(dt, { name: "evidence", label: e("Evidence"), required: !0, upload: !1, accept: "image/*,application/pdf", hint: e("A bank letter or the top of a statement, showing the account in your name.") })
      ] }) : /* @__PURE__ */ t(tn, { name: "mobile_no", label: e("Mobile No."), required: !0, hint: e("The number your pay should go to by mobile money.") }),
      /* @__PURE__ */ t(U, { name: "reason", label: e("Reason"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(he, { submitLabel: e("Send to HR"), onCancel: () => a(l.me), dirtyHint: !1 })
    ] })
  ] });
}
function la() {
  const a = D(), i = ve(), n = V(), o = oe(Z().name), { data: s, isLoading: c, error: r, mutate: u } = N(f.payoutRequestRecord, { name: o }), p = q(f.sendPayoutChange), v = q(f.withdrawPayoutChange), [y, d] = E(!1), h = async () => {
    try {
      await Vt(() => p.run({ name: o }), i.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it.")), await u();
    } catch {
    }
  }, R = s?.mine && s.status === "Draft" ? /* @__PURE__ */ t(w, { loading: p.loading, onClick: h, children: e("Send to HR") }) : s?.mine && s.status === "Waiting for HR" ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => d(!0), children: e("Withdraw") }) : void 0;
  return /* @__PURE__ */ m(
    Q,
    {
      title: s?.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
      subtitle: o,
      meta: s && /* @__PURE__ */ t(T, { value: s.status }),
      onBack: () => a(l.me),
      actions: R,
      loading: c,
      error: r,
      onRetry: u,
      children: [
        s && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
          p.errorMessage && /* @__PURE__ */ t($, { tone: "error", children: p.errorMessage }),
          s.status === "Waiting for HR" && /* @__PURE__ */ t($, { tone: "info", children: e("HR confirms it on the desk. You are told either way.") }),
          /* @__PURE__ */ t(
            J,
            {
              items: [
                { label: e("Bank"), value: s.bank, hideWhenEmpty: !0 },
                { label: e("Account No."), value: s.account_no, hideWhenEmpty: !0 },
                { label: e("Account Name"), value: s.account_name, hideWhenEmpty: !0 },
                { label: e("Mobile No."), value: s.mobile_no, hideWhenEmpty: !0 },
                { label: e("Provider"), value: s.provider, hideWhenEmpty: !0 },
                { label: e("Evidence"), value: s.change === "Bank Account" ? s.has_evidence ? e("Attached") : e("Missing") : null, hideWhenEmpty: !0 },
                { label: e("Sent On"), value: s.sent_on ? xe(s.sent_on) : null, hideWhenEmpty: !0 },
                { label: e("Effective From"), value: s.effective_from ? g(s.effective_from) : null, hideWhenEmpty: !0 },
                { label: e("Decision Note"), value: s.decision_note, hideWhenEmpty: !0, full: !0 },
                { label: e("Reason"), value: s.reason, hideWhenEmpty: !0, full: !0 }
              ]
            }
          )
        ] }),
        /* @__PURE__ */ t(
          pt,
          {
            open: y,
            onClose: () => d(!1),
            title: e("Withdraw this request?"),
            confirmLabel: e("Withdraw"),
            destructive: !0,
            onConfirm: async () => {
              await v.run({ name: o }), n.success(e("Request withdrawn.")), await u();
            },
            children: e("HR will not act on it. Your pay keeps going where it goes now.")
          }
        )
      ]
    }
  );
}
function ca() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.expenseList);
  return /* @__PURE__ */ t(
    ne,
    {
      title: e("Expense Claims"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.expenseNew), children: [
        /* @__PURE__ */ t(me, {}),
        e("New Expense Claim")
      ] }),
      children: c && !i?.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Fe, {}), title: e("No expense claims yet"), description: e("Claim what you spent for work, with a photo of each receipt.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i ?? []).map((r) => /* @__PURE__ */ t(
        M,
        {
          primary: B(r.total_claimed_amount, r.currency),
          secondary: g(r.posting_date || r.creation),
          action: /* @__PURE__ */ t(T, { value: r.docstatus === 0 ? r.approval_status || "Draft" : r.status }),
          onClick: () => a(l.expenseRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function da() {
  const a = D(), i = V(), n = N(f.expenseOptions), o = q(f.claimExpenses), s = ce(
    () => le.object({
      lines: le.array(le.object({ expense_type: we(() => e("Expense Type")), amount: ut(() => e("Amount"), { min: 0.01 }) }).loose()).min(1)
    }).loose(),
    []
  ), c = () => ({ lines: [{ expense_date: Y(), expense_type: "", amount: null, description: "" }], remark: "", receipts: [] }), r = de({ schema: s, defaultValues: c() }), u = Je(ve().user, "expense-claim", "new"), [p, v] = E(null);
  ye(() => {
    u.restored && Array.isArray(u.restored.value?.lines) && u.restored.value.lines.length && (r.reset({ ...c(), ...u.restored.value, receipts: [] }), v(u.restored.saved), u.dismiss());
    const h = r.watch((R) => u.keep({ lines: R.lines ?? [], remark: R.remark ?? "" }));
    return () => h.unsubscribe();
  }, []);
  const y = () => {
    u.clear(), v(null), r.reset(c());
  }, d = async (h) => {
    const R = await o.run({ lines: JSON.stringify(h.lines), remark: h.remark });
    u.clear();
    const x = [];
    for (const W of h.receipts ?? [])
      try {
        await st(W, { doctype: "Expense Claim", docname: R, isPrivate: !0 });
      } catch {
        x.push(W.name);
      }
    x.length ? i.warning(e("The claim was saved, but {0} receipts did not upload. Add them on a computer.", [String(x.length)])) : i.success(e("Claim sent to {0}.", [n.data?.approver_name ?? e("your expense approver")])), a(l.expenseRecord(R));
  };
  return /* @__PURE__ */ m(te, { title: e("New Expense Claim"), onBack: () => a(l.expenses), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    p !== null && /* @__PURE__ */ t($, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: y, children: e("Start Again") }), children: e("You started this claim on {0}. Add the receipts again before you send it.", [g(Ge(p))]) }),
    n.data && !n.data.approver_name && /* @__PURE__ */ t($, { tone: "warning", children: e("Nobody approves your expense claims yet. Ask HR to set an expense approver.") }),
    /* @__PURE__ */ m(ue, { form: r, onSubmit: d, children: [
      /* @__PURE__ */ t(
        ht,
        {
          name: "lines",
          label: e("Expenses"),
          minRows: 1,
          addLabel: e("Add an Expense"),
          newRow: () => ({ expense_date: Y(), expense_type: "", amount: null, description: "" }),
          renderRow: (h) => /* @__PURE__ */ m(fe, { children: [
            /* @__PURE__ */ t(Ae, { name: h("expense_type"), label: e("Expense Type"), required: !0, options: (n.data?.types ?? []).map((R) => ({ value: R.name, label: R.name, description: R.description ?? void 0 })) }),
            /* @__PURE__ */ t(je, { name: h("amount"), label: e("Amount ({0})", [n.data?.currency ?? ""]), required: !0, min: 0, step: 0.01 }),
            /* @__PURE__ */ t(re, { name: h("expense_date"), label: e("Date"), maxDate: Y() }),
            /* @__PURE__ */ t(U, { name: h("description"), label: e("Description") })
          ] })
        }
      ),
      /* @__PURE__ */ t(dt, { name: "receipts", label: e("Receipts"), multiple: !0, upload: !1, accept: "image/*,application/pdf", hint: e("Take a photo of each receipt, or choose a file. Only you, your approver and HR can open them.") }),
      /* @__PURE__ */ t(U, { name: "remark", label: e("Note"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(he, { submitLabel: e("Send Claim"), onCancel: () => a(l.expenses) })
    ] })
  ] });
}
function ua() {
  const a = D(), i = oe(Z().name), { data: n, isLoading: o, error: s, mutate: c } = N(f.expenseRecord, { name: i });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n ? B(n.total_claimed_amount, n.currency) : e("Expense Claim"),
      subtitle: n && (n.mine ? i : n.employee_name),
      meta: n && /* @__PURE__ */ t(T, { value: n.docstatus === 0 ? n.approval_status || "Draft" : n.status }),
      onBack: () => a(l.expenses),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        /* @__PURE__ */ t(
          J,
          {
            items: [
              { label: e("Claimed"), value: B(n.total_claimed_amount, n.currency) },
              { label: e("Approved Amount"), value: n.docstatus === 1 ? B(n.total_sanctioned_amount, n.currency) : null, hideWhenEmpty: !0 },
              { label: e("Expense Approver"), value: n.approver_name, hideWhenEmpty: !0 },
              { label: e("Note"), value: n.remark, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(F, { title: e("Expenses"), children: /* @__PURE__ */ t(L, { divided: !0, children: n.expenses.map((r, u) => /* @__PURE__ */ t(M, { primary: `${r.expense_type} · ${B(r.amount, n.currency)}`, secondary: [g(r.expense_date), r.description ?? ""].filter(Boolean).join(" · ") }, u)) }) }),
        n.receipts.length > 0 && /* @__PURE__ */ t(F, { title: e("Receipts"), children: /* @__PURE__ */ t(L, { divided: !0, children: n.receipts.map((r) => /* @__PURE__ */ t(M, { primary: r.file_name, href: r.file_url }, r.name)) }) })
      ] })
    }
  );
}
function ha() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.advanceList);
  return /* @__PURE__ */ t(
    ne,
    {
      title: e("Advances"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.advanceNew), children: [
        /* @__PURE__ */ t(me, {}),
        e("Request an Advance")
      ] }),
      children: c && !i?.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Nt, {}), title: e("No advances"), description: e("Money paid to you ahead of work shows here, with what is left to settle.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i ?? []).map((r) => /* @__PURE__ */ t(
        M,
        {
          primary: r.purpose,
          secondary: r.to_settle > 0 ? e("{0} · {1} left to settle", [B(r.advance_amount, r.currency), B(r.to_settle, r.currency)]) : B(r.advance_amount, r.currency),
          action: /* @__PURE__ */ t(T, { value: r.docstatus === 0 ? "Draft" : r.status }),
          onClick: () => a(l.advanceRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function ma() {
  const a = D(), i = V(), n = q(f.requestAdvance), o = ce(() => le.object({ purpose: we(() => e("Purpose")), amount: ut(() => e("Amount"), { min: 1 }) }), []), s = de({ schema: o, defaultValues: { purpose: "", amount: null } });
  return /* @__PURE__ */ t(te, { title: e("Request an Advance"), onBack: () => a(l.advances), children: /* @__PURE__ */ m(
    ue,
    {
      form: s,
      onSubmit: async (c) => {
        const r = await n.run({ purpose: c.purpose, amount: c.amount });
        i.success(e("Advance requested.")), a(l.advanceRecord(r));
      },
      children: [
        /* @__PURE__ */ t(U, { name: "purpose", label: e("Purpose"), required: !0, multiline: !0, rows: 2, hint: e("What the money is for, e.g. a field visit.") }),
        /* @__PURE__ */ t(je, { name: "amount", label: e("Amount"), required: !0, min: 1, step: 1 }),
        /* @__PURE__ */ t(he, { submitLabel: e("Request"), onCancel: () => a(l.advances) })
      ]
    }
  ) });
}
function pa() {
  const a = D(), i = oe(Z().name), { data: n, isLoading: o, error: s, mutate: c } = N(f.advanceRecord, { name: i });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n?.purpose ?? e("Advance"),
      subtitle: n && (n.mine ? i : n.employee_name),
      meta: n && /* @__PURE__ */ t(T, { value: n.docstatus === 0 ? "Draft" : n.status }),
      onBack: () => a(l.advances),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ t(
        J,
        {
          items: [
            { label: e("Amount"), value: B(n.advance_amount, n.currency) },
            { label: e("Paid"), value: B(n.paid_amount, n.currency) },
            { label: e("Claimed"), value: B(n.claimed_amount, n.currency) },
            { label: e("Returned"), value: B(n.return_amount, n.currency) },
            { label: e("Left to Settle"), value: B(n.to_settle, n.currency) },
            { label: e("Requested On"), value: g(n.posting_date) }
          ]
        }
      )
    }
  );
}
function ya() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.payslips);
  return /* @__PURE__ */ t(ne, { title: e("Payslips"), onBack: () => a(""), loading: n, error: o, onRetry: s, children: c && !i?.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(It, {}), title: e("No payslips yet"), description: e("Your payslips show here once payroll is run.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i ?? []).map((r) => /* @__PURE__ */ t(
    M,
    {
      primary: e("{0} to {1}", [g(r.start_date), g(r.end_date)]),
      secondary: e("Net pay {0}", [B(r.net_pay, r.currency)]),
      onClick: () => a(l.payRecord(r.name))
    },
    r.name
  )) }) });
}
function fa() {
  const a = D(), i = oe(Z().name), { data: n, isLoading: o, error: s, mutate: c } = N(f.payslipRecord, { name: i });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n ? e("{0} to {1}", [g(n.start_date), g(n.end_date)]) : e("Payslip"),
      subtitle: n?.employee_name,
      onBack: () => a(l.pay),
      actions: /* @__PURE__ */ m(w, { href: Mn(i), target: "_blank", rel: "noopener", children: [
        /* @__PURE__ */ t(xn, {}),
        e("Open Payslip")
      ] }),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        /* @__PURE__ */ t(
          J,
          {
            items: [
              { label: e("Gross Pay"), value: B(n.gross_pay, n.currency) },
              { label: e("Total Deduction"), value: B(n.total_deduction, n.currency) },
              { label: e("Net Pay"), value: B(n.net_pay, n.currency) }
            ]
          }
        ),
        /* @__PURE__ */ t(F, { title: e("Earnings"), children: /* @__PURE__ */ t(L, { divided: !0, children: n.earnings.map((r) => /* @__PURE__ */ t(M, { primary: r.component, action: B(r.amount, n.currency) }, r.component)) }) }),
        /* @__PURE__ */ t(F, { title: e("Deductions"), children: /* @__PURE__ */ t(L, { divided: !0, children: n.deductions.map((r) => /* @__PURE__ */ t(M, { primary: r.component, action: B(r.amount, n.currency) }, r.component)) }) })
      ] })
    }
  );
}
function va() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.timesheets);
  return /* @__PURE__ */ m(
    ne,
    {
      title: e("Timesheets"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: i?.weekly ? /* @__PURE__ */ m(w, { onClick: () => a(l.week(Ve(Y()))), children: [
        /* @__PURE__ */ t(Be, {}),
        e("This Week")
      ] }) : void 0,
      children: [
        i && !i.weekly && /* @__PURE__ */ t($, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer; they show here.") }),
        c && !i?.timesheets.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Be, {}), title: e("No timesheets yet"), description: e("Your timesheets show here, newest first.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i?.timesheets ?? []).map((r) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} to {1}", [g(r.start_date), g(r.end_date)]),
            secondary: e("{0} hours", [String(r.total_hours ?? 0)]),
            action: /* @__PURE__ */ t(T, { value: r.docstatus === 1 ? "Approved" : r.custom_approval_state || r.status }),
            onClick: () => a(i?.weekly && r.custom_week_start ? l.week(r.custom_week_start) : l.timesheetRecord(r.name))
          },
          r.name
        )) })
      ]
    }
  );
}
function nt(a) {
  return a === "Rest day" ? e("Rest Day") : a === "Public holiday" ? e("Public Holiday") : null;
}
function at(a) {
  const i = ((/* @__PURE__ */ new Date(`${a}T12:00:00Z`)).getUTCDay() + 6) % 7;
  return [e("Monday"), e("Tuesday"), e("Wednesday"), e("Thursday"), e("Friday"), e("Saturday"), e("Sunday")][i];
}
function ga() {
  const a = D(), i = V(), n = Ve(Z().week || Y()), { data: o, isLoading: s, error: c, mutate: r } = N(f.timesheetWeek, { week_start: n }), u = q(f.saveTimesheetWeek), p = q(f.timesheetClaim), [v, y] = E([]), [d, h] = E(() => {
    const b = Y();
    return b >= n && b <= pe(n, 6) ? Ie(n).indexOf(b) : 0;
  }), [R, x] = E(!1), W = Re(!1), S = (b) => {
    W.current = b, x(b);
  }, A = Je(ve().user, "timesheet-week", n), [P, j] = E(null), I = (b) => b.timesheet?.entries.length ? b.timesheet.entries : [et([], b.default_activity_type)], G = Re(null);
  ye(() => {
    if (!o || o.week_start !== n) return;
    const b = G.current === n;
    if (G.current = n, b && W.current) return;
    const K = o.weekly && (!o.timesheet || o.timesheet.can_edit), z = A.key ? Oe(A.key) : null;
    if (z && K && Array.isArray(z.value) && z.value.length) {
      y(z.value), S(!0), j(z.saved);
      return;
    }
    z && A.key && jt(A.key), y(I(o)), S(!1), j(null);
  }, [o, n]);
  const O = Ie(n), _ = o?.days[d], k = !!o?.weekly && (!o.timesheet || o.timesheet.can_edit), Ne = ce(() => (o?.activity_types ?? []).map((b) => ({ value: b, label: b })), [o]), ie = (b) => {
    y(b), S(!0), A.keep(b);
  }, Ut = () => {
    A.clear(), j(null), o && y(I(o)), S(!1);
  }, Ke = async (b) => {
    try {
      const K = await u.run({ week_start: n, entries: JSON.stringify(Pn(v)), send: b ? 1 : 0 });
      return i.success(b ? e("Week sent for approval.") : e("Week saved.")), A.clear(), j(null), S(!1), await r(), K;
    } catch {
      return null;
    }
  }, Jt = o?.timesheet?.can_claim ? /* @__PURE__ */ t(
    w,
    {
      onClick: async () => {
        try {
          a(l.toilRecord(await p.run({ name: o.timesheet.name })));
        } catch {
        }
      },
      loading: p.loading,
      children: e("Claim as Time Off in Lieu")
    }
  ) : k ? /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(w, { variant: "outline", loading: u.loading, disabled: !R, onClick: () => Ke(!1), children: e("Save") }),
    o?.approval && /* @__PURE__ */ t(w, { loading: u.loading, onClick: () => Ke(!0), children: e("Send for Approval") })
  ] }) : void 0;
  return /* @__PURE__ */ t(
    te,
    {
      title: e("Week of {0}", [g(n)]),
      subtitle: e("{0} hours this week", [String(Tn(v))]),
      meta: o?.timesheet && /* @__PURE__ */ t(T, { value: o.timesheet.docstatus === 1 ? "Approved" : o.timesheet.state }),
      onBack: () => a(l.timesheet),
      actions: Jt,
      loading: s,
      error: c,
      onRetry: r,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        (u.errorMessage || p.errorMessage) && /* @__PURE__ */ t($, { tone: "error", children: u.errorMessage || p.errorMessage }),
        P !== null && /* @__PURE__ */ t(
          $,
          {
            tone: "info",
            title: e("Restored From This Phone"),
            action: /* @__PURE__ */ t(w, { onClick: Ut, children: e("Discard") }),
            children: e("What you entered on {0} was not saved yet. Save or send it when you are ready.", [g(Ge(P))])
          }
        ),
        !o.weekly && /* @__PURE__ */ t($, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer.") }),
        o.timesheet?.state === "Returned" && o.timesheet.return_reason && /* @__PURE__ */ t($, { tone: "warning", title: e("Returned to You"), children: o.timesheet.return_reason }),
        /* @__PURE__ */ m("div", { className: "flex items-center justify-between gap-2", children: [
          /* @__PURE__ */ t(Le, { label: e("Previous Day"), variant: "outline", onClick: () => d > 0 ? h(d - 1) : a(l.week(pe(n, -7))), children: /* @__PURE__ */ t(Cn, {}) }),
          /* @__PURE__ */ m("div", { className: "flex flex-col items-center", children: [
            /* @__PURE__ */ t(ee, { size: "lg", children: at(O[d]) }),
            /* @__PURE__ */ t(ee, { size: "sm", muted: !0, children: g(O[d]) })
          ] }),
          /* @__PURE__ */ t(Le, { label: e("Next Day"), variant: "outline", onClick: () => d < 6 ? h(d + 1) : a(l.week(pe(n, 7))), children: /* @__PURE__ */ t(kt, {}) })
        ] }),
        /* @__PURE__ */ m("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ t(ge, { children: e("{0} hours entered", [String(zt(v, d))]) }),
          _?.attendance_hours !== null && _?.attendance_hours !== void 0 && /* @__PURE__ */ t(ge, { variant: "outline", children: e("Attendance {0} hours", [String(_.attendance_hours)]) }),
          _ && nt(_.kind) && /* @__PURE__ */ t(ge, { tone: "info", children: nt(_.kind) }),
          _?.leave && /* @__PURE__ */ t(ge, { tone: "warning", children: _.leave_fraction === 0.5 ? e("Half Day of Leave") : e("On Leave") })
        ] }),
        v.map((b) => /* @__PURE__ */ t(cn, { children: /* @__PURE__ */ m(dn, { className: "flex flex-col gap-3", children: [
          /* @__PURE__ */ m("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(Ce, { htmlFor: `activity-${b.row}`, children: e("Activity Type") }),
            /* @__PURE__ */ t(
              un,
              {
                id: `activity-${b.row}`,
                value: b.activity_type,
                options: Ne,
                disabled: !k,
                onValueChange: (K) => ie(v.map((z) => z.row === b.row ? { ...z, activity_type: K } : z))
              }
            )
          ] }),
          /* @__PURE__ */ m("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(Ce, { htmlFor: `description-${b.row}`, children: e("Description") }),
            /* @__PURE__ */ t(
              qe,
              {
                id: `description-${b.row}`,
                value: b.description ?? "",
                disabled: !k,
                onChange: (K) => ie(v.map((z) => z.row === b.row ? { ...z, description: K.target.value } : z))
              }
            )
          ] }),
          /* @__PURE__ */ m("div", { className: "flex items-end gap-2", children: [
            /* @__PURE__ */ m("div", { className: "flex flex-1 flex-col gap-1", children: [
              /* @__PURE__ */ t(Ce, { htmlFor: `hours-${b.row}`, children: e("Hours on {0}", [at(O[d])]) }),
              /* @__PURE__ */ t(
                qe,
                {
                  id: `hours-${b.row}`,
                  type: "number",
                  inputMode: "decimal",
                  min: 0,
                  max: 24,
                  step: 0.25,
                  value: b.hours[d] ? String(b.hours[d]) : "",
                  disabled: !k,
                  onChange: (K) => ie(Bn(v, b.row, d, K.target.value))
                }
              )
            ] }),
            k && v.length > 1 && /* @__PURE__ */ t(Le, { label: e("Remove Line"), variant: "ghost", onClick: () => ie(v.filter((K) => K.row !== b.row)), children: /* @__PURE__ */ t(Ln, {}) })
          ] })
        ] }) }, b.row)),
        k && /* @__PURE__ */ m("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ m(w, { variant: "outline", onClick: () => ie([...v, et(v, o.default_activity_type)]), children: [
            /* @__PURE__ */ t(me, {}),
            e("Add Line")
          ] }),
          o.previous_entries.length > 0 && /* @__PURE__ */ m(w, { variant: "outline", onClick: () => ie(Hn(o.previous_entries)), children: [
            /* @__PURE__ */ t(Rn, {}),
            e("Copy Last Week")
          ] })
        ] }),
        o.checks.length > 0 && /* @__PURE__ */ t(F, { title: e("Weekly Check"), children: /* @__PURE__ */ t(L, { divided: !0, children: o.checks.map((b) => /* @__PURE__ */ t(M, { primary: b }, b)) }) })
      ] })
    }
  );
}
function _a() {
  const a = D(), i = oe(Z().name), { data: n, isLoading: o, error: s, mutate: c } = N(f.timesheetRecord, { name: i });
  return /* @__PURE__ */ t(
    Q,
    {
      title: e("Timesheet"),
      subtitle: n && (n.mine ? i : n.employee_name),
      meta: n && /* @__PURE__ */ t(T, { value: n.docstatus === 1 ? "Approved" : n.state }),
      onBack: () => a(l.timesheet),
      actions: n?.mine && n.week_start ? /* @__PURE__ */ t(w, { onClick: () => a(l.week(n.week_start)), children: e("Open the Week") }) : void 0,
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          J,
          {
            items: [
              { label: e("From"), value: g(n.start_date) },
              { label: e("To"), value: g(n.end_date) },
              { label: e("Total Hours"), value: String(n.total_hours ?? 0) }
            ]
          }
        ),
        /* @__PURE__ */ t(L, { divided: !0, children: n.lines.map((r, u) => /* @__PURE__ */ t(M, { primary: e("{0} · {1} hours", [g(r.date), String(r.hours)]), secondary: [r.activity_type, r.description].filter(Boolean).join(" · ") }, u)) })
      ] })
    }
  );
}
function ka() {
  const a = D(), { data: i, isLoading: n, error: o, mutate: s, hasLoaded: c } = N(f.toilList);
  return /* @__PURE__ */ m(
    ne,
    {
      title: e("Time Off in Lieu"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: i?.eligible ? /* @__PURE__ */ m(w, { onClick: () => a(l.toilNew), children: [
        /* @__PURE__ */ t(me, {}),
        e("Claim Time Off")
      ] }) : void 0,
      children: [
        i && !i.eligible && /* @__PURE__ */ t($, { tone: "info", children: e("Your grade does not bank extra hours as time off. Ask HR if you think it should.") }),
        i?.eligible && /* @__PURE__ */ m(yt, { columns: 2, children: [
          /* @__PURE__ */ t(Ee, { label: e("Days Left"), value: String(i.left) }),
          /* @__PURE__ */ t(
            Ee,
            {
              label: e("Lapsing in 30 Days"),
              value: String(i.lapsing),
              hint: i.first_lapse ? e("First on {0}", [g(i.first_lapse)]) : void 0
            }
          )
        ] }),
        c && !i?.claims.length ? /* @__PURE__ */ t(ae, { icon: /* @__PURE__ */ t(Pe, {}), title: e("No claims yet"), description: e("Claim the extra hours you worked, a day at a time.") }) : /* @__PURE__ */ t(L, { divided: !0, children: (i?.claims ?? []).map((r) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} hours · {1} days", [String(r.total_hours ?? 0), String(r.days ?? 0)]),
            secondary: r.status === "Approved" && r.lapses_on ? e("{0} days left, usable until {1}", [String(r.days_left ?? 0), g(r.lapses_on)]) : g(r.creation),
            action: /* @__PURE__ */ t(T, { value: r.status }),
            onClick: () => a(l.toilRecord(r.name))
          },
          r.name
        )) })
      ]
    }
  );
}
const ot = () => ({ work_date: "", hours: null, work_done: "" });
function wa() {
  const a = D(), i = V(), [n] = rt(), o = n.get("claim"), s = N(f.toilList), c = N(f.toilRecord, { name: o ?? "" }, { enabled: !!o }), r = q(f.saveToilClaim), u = en(), [p, v] = E(!1), [y, d] = E(null), h = de({ defaultValues: { lines: [ot()], note: "" } });
  ye(() => {
    c.data && h.reset({ lines: c.data.lines.map((S) => ({ work_date: S.work_date, hours: S.hours, work_done: S.work_done })), note: c.data.note ?? "" });
  }, [c.data, h]);
  const R = async () => {
    if (s.data) {
      v(!0), d(null);
      try {
        const S = s.data.from_attendance ? "Attendance" : "Timesheet", A = Y(), P = await u.get(f.extraTime, { employee: s.data.employee, from_date: pe(A, -30), to_date: A, source: S }) ?? [], j = h.getValues("lines").filter((I) => I.work_date);
        h.setValue("lines", ta(j, P), { shouldDirty: !0 }), d(P.length ? e("{0} days found in the last 30 days. Say what the work was on each.", [String(P.length)]) : e("The records show no extra hours you have not claimed in the last 30 days."));
      } catch {
        d(e("The records could not be read. Enter the days yourself."));
      } finally {
        v(!1);
      }
    }
  }, x = async (S) => {
    const A = await r.run({ lines: JSON.stringify(S.lines.filter((P) => P.work_date)), note: S.note, name: o ?? void 0 });
    i.success(e("Claim saved. Send it when it is ready.")), a(l.toilRecord(A));
  }, W = s.data && (s.data.from_attendance || s.data.from_timesheets);
  return /* @__PURE__ */ m(
    te,
    {
      title: o ? e("Change Claim") : e("Claim Time Off"),
      onBack: () => a(o ? l.toilRecord(o) : l.toil),
      loading: s.isLoading || c.isLoading,
      error: s.error ?? c.error,
      actions: W ? /* @__PURE__ */ t(w, { variant: "outline", loading: p, onClick: R, children: e("Fill from Records") }) : void 0,
      children: [
        y && /* @__PURE__ */ t($, { tone: "info", children: y }),
        /* @__PURE__ */ m(ue, { form: h, onSubmit: x, children: [
          /* @__PURE__ */ t(
            ht,
            {
              name: "lines",
              label: e("Days Worked"),
              minRows: 1,
              addLabel: e("Add a Day"),
              newRow: ot,
              renderRow: (S) => /* @__PURE__ */ m(fe, { children: [
                /* @__PURE__ */ t(re, { name: S("work_date"), label: e("Date"), required: !0, maxDate: Y() }),
                /* @__PURE__ */ t(je, { name: S("hours"), label: e("Hours Worked"), min: 0, max: 24, step: 0.25 }),
                /* @__PURE__ */ t(U, { name: S("work_done"), label: e("Work Done"), required: !0, multiline: !0, rows: 2 })
              ] })
            }
          ),
          /* @__PURE__ */ t(U, { name: "note", label: e("Note"), multiline: !0, rows: 2, hint: e("Anything your approver should know about these days.") }),
          /* @__PURE__ */ t(he, { submitLabel: e("Save Claim"), onCancel: () => a(o ? l.toilRecord(o) : l.toil) })
        ] })
      ]
    }
  );
}
function ba() {
  const a = D(), i = V(), n = oe(Z().name), { data: o, isLoading: s, error: c, mutate: r } = N(f.toilRecord, { name: n }), u = q(f.toilAction), p = async (y) => {
    try {
      await u.run({ name: n, action: y }), i.success(e("Claim sent.")), await r();
    } catch {
    }
  }, v = o && /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    o.can_edit && /* @__PURE__ */ t(w, { variant: "outline", onClick: () => a(`${l.toilNew}?claim=${encodeURIComponent(n)}`), children: e("Change") }),
    o.actions.map((y) => /* @__PURE__ */ t(w, { loading: u.loading, onClick: () => p(y), children: y === "Send for Authorisation" ? e("Send for Authorisation") : e("Send for Approval") }, y)),
    o.mine && o.status === "Approved" && (o.days_left ?? 0) > 0 && o.leave_type && /* @__PURE__ */ t(w, { onClick: () => a(`${l.leaveNew}?type=${encodeURIComponent(o.leave_type ?? "")}`), children: e("Apply for Leave") })
  ] });
  return /* @__PURE__ */ t(
    Q,
    {
      title: e("Time Off in Lieu Claim"),
      subtitle: o && !o.mine ? o.employee_name : n,
      meta: o && /* @__PURE__ */ t(T, { value: o.status }),
      onBack: () => a(l.toil),
      actions: v,
      loading: s,
      error: c,
      onRetry: r,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        u.errorMessage && /* @__PURE__ */ t($, { tone: "error", children: u.errorMessage }),
        o.stage.items.length > 0 && /* @__PURE__ */ t($, { tone: o.stage.tone, children: /* @__PURE__ */ t("div", { className: "flex flex-col gap-1", children: o.stage.items.map((y) => /* @__PURE__ */ m(ee, { children: [
          /* @__PURE__ */ m("strong", { children: [
            y.label,
            ":"
          ] }),
          " ",
          y.text
        ] }, y.label)) }) }),
        /* @__PURE__ */ t(
          J,
          {
            items: [
              { label: e("Total Extra Hours"), value: String(o.total_hours ?? 0) },
              { label: e("Time Off (Days)"), value: String(o.days ?? 0) },
              { label: e("Approver"), value: o.approver_name, hideWhenEmpty: !0 },
              { label: e("Days Left"), value: o.days_left === null ? null : String(o.days_left), hideWhenEmpty: !0 },
              { label: e("Usable Until"), value: o.lapses_on ? g(o.lapses_on) : null, hideWhenEmpty: !0 },
              { label: e("Note"), value: o.note, hideWhenEmpty: !0, full: !0 },
              { label: e("Approver's Note"), value: o.decision_note, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(F, { title: e("Days Worked"), children: /* @__PURE__ */ t(L, { divided: !0, children: o.lines.map((y) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} · {1} hours", [g(y.work_date), String(y.hours ?? y.planned_hours ?? 0)]),
            secondary: [y.work_done, y.supported_by ?? ""].filter(Boolean).join(" · ")
          },
          y.work_date
        )) }) })
      ] })
    }
  );
}
const Ca = [
  { path: "leave", element: /* @__PURE__ */ t(aa, {}) },
  { path: "leave/new", element: /* @__PURE__ */ t(oa, {}) },
  { path: "leave/:name", element: /* @__PURE__ */ t(ia, {}) },
  { path: "cover", element: /* @__PURE__ */ t(Vn, {}) },
  { path: "cover/:name", element: /* @__PURE__ */ t(Un, {}) },
  { path: "toil", element: /* @__PURE__ */ t(ka, {}) },
  { path: "toil/new", element: /* @__PURE__ */ t(wa, {}) },
  { path: "toil/:name", element: /* @__PURE__ */ t(ba, {}) },
  { path: "timesheet", element: /* @__PURE__ */ t(va, {}) },
  { path: "timesheet/week/:week", element: /* @__PURE__ */ t(ga, {}) },
  { path: "timesheet/:name", element: /* @__PURE__ */ t(_a, {}) },
  { path: "expenses", element: /* @__PURE__ */ t(ca, {}) },
  { path: "expenses/new", element: /* @__PURE__ */ t(da, {}) },
  { path: "expenses/:name", element: /* @__PURE__ */ t(ua, {}) },
  { path: "advances", element: /* @__PURE__ */ t(ha, {}) },
  { path: "advances/new", element: /* @__PURE__ */ t(ma, {}) },
  { path: "advances/:name", element: /* @__PURE__ */ t(pa, {}) },
  { path: "pay", element: /* @__PURE__ */ t(ya, {}) },
  { path: "pay/:name", element: /* @__PURE__ */ t(fa, {}) },
  { path: "check-in", element: /* @__PURE__ */ t(In, {}) },
  { path: "attendance", element: /* @__PURE__ */ t(On, {}) },
  { path: "attendance/new", element: /* @__PURE__ */ t(zn, {}) },
  { path: "attendance/:name", element: /* @__PURE__ */ t(tt, { doctype: "Attendance Request" }) },
  { path: "shifts", element: /* @__PURE__ */ t(jn, {}) },
  { path: "shifts/new", element: /* @__PURE__ */ t(Yn, {}) },
  { path: "shifts/:name", element: /* @__PURE__ */ t(tt, { doctype: "Shift Request" }) },
  { path: "me", element: /* @__PURE__ */ t(ra, {}) },
  { path: "me/payout/new", element: /* @__PURE__ */ t(sa, {}) },
  { path: "me/payout/:name", element: /* @__PURE__ */ t(la, {}) }
], Wa = Xt({
  key: "seal_hrms.my_hr",
  home: Jn,
  routes: Ca,
  records: ft,
  settings: [{ key: "hr_notifications", label: "HR", kind: "push-category" }]
});
export {
  Ca as ROUTES,
  Wa as default
};
