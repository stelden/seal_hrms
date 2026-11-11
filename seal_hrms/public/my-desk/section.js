var rn = Object.defineProperty;
var sn = (a, r, n) => r in a ? rn(a, r, { enumerable: !0, configurable: !0, writable: !0, value: n }) : a[r] = n;
var it = (a, r, n) => sn(a, typeof r != "symbol" ? r + "" : r, n);
import { jsx as t, jsxs as m, Fragment as de } from "react/jsx-runtime";
import { useShell as ne, defineSection as ln } from "@stelden/seal-frontend/section";
import { useContext as cn, createContext as dn, forwardRef as yt, createElement as Ie, useCallback as Ae, useState as q, useMemo as me, useRef as be, useEffect as ue } from "react";
import { useParams as Z, useSearchParams as ft } from "react-router";
import { useGet as A, usePost as W, formatDateTime as Ce, formatDate as _, uploadFile as vt, formatCurrency as F, useFrappeCall as un } from "@stelden/seal-frontend";
import { z as ee, required as le, frappeDate as Re, useSealForm as pe, SealForm as ye, RadioInput as gt, DateInput as he, CheckboxInput as Ze, TextInput as H, FormActions as fe, SelectInput as se, FormSection as st, AutocompleteInput as Ee, FileInput as _t, MobileInputKE as hn, amount as kt, RowsInput as De, NumberInput as Te, DateTimeInput as lt } from "@stelden/seal-frontend/forms";
import { __ as e, toneMap as mn, StatusChip as pn, useNotify as O, FormPage as ae, Alert as S, Button as w, Text as te, Section as B, List as T, ListItem as M, ListPage as oe, EmptyState as re, DetailPage as Q, DescriptionList as U, TabsNav as yn, TabPanel as Pe, SealDialog as wt, Textarea as fn, ConfirmDialog as bt, DashboardPage as vn, StatGrid as Ct, StatCard as ze, Badge as we, FilterChips as gn, Label as Ne, Input as je, IconButton as Fe, Card as _n, CardContent as kn, Select as wn } from "@stelden/seal-frontend/ui";
const X = (a) => encodeURIComponent(a);
function ie(a) {
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
  payoutRecord: (a) => `me/payout/${X(a)}`,
  travel: "travel",
  travelNew: "travel/new",
  travelRecord: (a) => `travel/${X(a)}`
}, Rt = {
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
  "Payout Change Request": { list: l.me, record: l.payoutRecord, create: l.payoutNew },
  "Travel Request": { list: l.travel, record: l.travelRecord, create: l.travelNew }
};
function bn(a) {
  return Rt[a]?.list;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Cn = (a) => a?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function Rn(a, r, n = []) {
  if (r == null)
    throw new Error("[lucide]: iconNode is required when icon name is used");
  return {
    name: Cn(a),
    size: 24,
    node: r,
    ...n.length > 0 ? { aliases: n } : {}
  };
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const xn = (a) => {
  let r = "", n = !1;
  for (const o of a) {
    if (o === "-" || o === "_" || o <= " ") {
      n = r.length > 0;
      continue;
    }
    r.length === 0 ? r += o.toLowerCase() : r += n ? o.toUpperCase() : o, n = !1;
  }
  return r;
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const An = (a) => {
  const r = xn(a);
  return r.charAt(0).toUpperCase() + r.slice(1);
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ye = (...a) => a.filter((r, n, o) => !!r && r.trim() !== "" && o.indexOf(r) === n).join(" ").trim();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ge = {
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
function Be(a) {
  return a != null;
}
function Nn(a, r = {}) {
  const n = r.attributeNames ?? {}, o = (h) => n[h] ?? h, s = a.size ?? a.width ?? ge.width, c = a.size ?? a.height ?? ge.height, i = a.aliases?.filter((h) => typeof h == "string" && h.trim() !== "").map((h) => `lucide-${h}`) ?? [], d = [...a.name ? [`lucide-${a.name}`] : [], ...i], y = r.className?.split(" ").filter(Boolean) ?? [], p = r.includeDefaultClasses === !1 ? Ye(...y) : Ye("lucide", ...d, ...y), f = r.absoluteStrokeWidth ? Number(r.strokeWidth ?? ge["stroke-width"]) * Number(a.size ?? a.width ?? ge.width) / Number(r.size ?? r.width ?? ge.width) : r.strokeWidth ?? ge["stroke-width"];
  return [
    "svg",
    {
      ...Object.entries(ge).reduce((h, [g, x]) => (h[o(g)] = x, h), {}),
      ..."color" in r && r.color && {
        [o("stroke")]: r.color
      },
      ..."size" in r && Be(r.size) && {
        [o("width")]: r.size,
        [o("height")]: r.size
      },
      ..."width" in r && Be(r.width) && {
        [o("width")]: r.width
      },
      ..."height" in r && Be(r.height) && {
        [o("height")]: r.height
      },
      [o("stroke-width")]: f,
      ...p && {
        [o("class")]: p
      },
      [o("viewBox")]: `0 0 ${s} ${c}`,
      ...r.hasA11yProp === !1 ? {
        [o("aria-hidden")]: "true"
      } : {},
      ..."attributes" in r && r.attributes
    },
    a.node.map((h) => {
      const [g, x, E] = h, D = r.nonScalingStroke ? { [o("vector-effect")]: "non-scaling-stroke", ...x } : x;
      return E ? [g, D, E] : [g, D];
    })
  ];
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function Sn(a, r = {}) {
  return Nn(a, {
    ...r,
    attributeNames: {
      ...r.attributeNames,
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
const Dn = (a) => {
  for (const r in a)
    if (r.startsWith("aria-") || r === "role" || r === "title")
      return !0;
  return !1;
}, Ln = dn({}), Tn = () => cn(Ln), Mn = yt(
  ({
    color: a,
    size: r,
    width: n,
    height: o,
    strokeWidth: s,
    absoluteStrokeWidth: c,
    nonScalingStroke: i,
    className: d = "",
    children: y,
    iconNode: p = [],
    icon: f = {
      node: p,
      aliases: [],
      size: 24
    },
    ...u
  }, h) => {
    const {
      size: g = 24,
      strokeWidth: x = 2,
      absoluteStrokeWidth: E = !1,
      nonScalingStroke: D = !1,
      color: L = "currentColor",
      className: I = ""
    } = Tn() ?? {}, V = !!y || Dn(u), [z, G, j = []] = Sn(f, {
      color: a ?? L,
      width: n ?? r ?? g,
      height: o ?? r ?? g,
      strokeWidth: s ?? x,
      absoluteStrokeWidth: c ?? E,
      nonScalingStroke: i ?? D,
      className: Ye(I, d),
      hasA11yProp: V,
      attributes: u
    });
    return Ie(
      z,
      {
        ref: h,
        ...G
      },
      [
        ...j.map(([b, C]) => Ie(b, C)),
        ...Array.isArray(y) ? y : [y]
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
function P(a, r = [], n = []) {
  const o = typeof a == "string" ? Rn(a, r, n) : a, s = yt(
    ({ className: c, ...i }, d) => Ie(Mn, {
      ref: d,
      icon: o,
      className: c,
      ...i
    })
  );
  return o.name && (s.displayName = An(o.name)), s;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const xt = {
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
xt.node;
const Ve = P(xt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const At = {
  name: "chevron-left",
  size: 24,
  node: [["path", { d: "m15 18-6-6 6-6", key: "1wnfg3" }]]
};
At.node;
const qn = P(At);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Nt = {
  name: "chevron-right",
  size: 24,
  node: [["path", { d: "m9 18 6-6-6-6", key: "mthhwq" }]]
};
Nt.node;
const St = P(Nt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Dt = {
  name: "clock",
  size: 24,
  node: [
    ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
    ["path", { d: "M12 6v6l4 2", key: "mmk7yg" }]
  ]
};
Dt.node;
const Ue = P(Dt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Lt = {
  name: "copy",
  size: 24,
  node: [
    ["rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2", key: "17jyea" }],
    ["path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2", key: "zix9uf" }]
  ]
};
Lt.node;
const Wn = P(Lt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Tt = {
  name: "download",
  size: 24,
  node: [
    ["path", { d: "M12 15V3", key: "m9g1x1" }],
    ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
    ["path", { d: "m7 10 5 5 5-5", key: "brsn70" }]
  ]
};
Tt.node;
const $n = P(Tt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Mt = {
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
Mt.node;
const En = P(Mt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const qt = {
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
qt.node;
const ct = P(qt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Wt = {
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
Wt.node;
const $t = P(Wt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Et = {
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
Et.node;
const Je = P(Et);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Pt = {
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
Pt.node;
const Pn = P(Pt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ft = {
  name: "log-in",
  size: 24,
  node: [
    ["path", { d: "m10 17 5-5-5-5", key: "1bsop3" }],
    ["path", { d: "M15 12H3", key: "6jk70r" }],
    ["path", { d: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4", key: "u53s6r" }]
  ]
};
Ft.node;
const Fn = P(Ft);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Bt = {
  name: "log-out",
  size: 24,
  node: [
    ["path", { d: "m16 17 5-5-5-5", key: "1bji2h" }],
    ["path", { d: "M21 12H9", key: "dn1m92" }],
    ["path", { d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", key: "1uf3rs" }]
  ]
};
Bt.node;
const Bn = P(Bt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ht = {
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
Ht.node;
const Qe = P(Ht);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ot = {
  name: "plane",
  size: 24,
  node: [
    [
      "path",
      {
        d: "M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z",
        key: "1v9wt8"
      }
    ]
  ]
};
Ot.node;
const It = P(Ot);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const zt = {
  name: "plus",
  size: 24,
  node: [
    ["path", { d: "M5 12h14", key: "1ays0h" }],
    ["path", { d: "M12 5v14", key: "s699le" }]
  ]
};
zt.node;
const ve = P(zt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const jt = {
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
jt.node;
const Ge = P(jt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Yt = {
  name: "repeat",
  size: 24,
  node: [
    ["path", { d: "m17 2 4 4-4 4", key: "nntrym" }],
    ["path", { d: "M3 11v-1a4 4 0 0 1 4-4h14", key: "84bu3i" }],
    ["path", { d: "m7 22-4-4 4-4", key: "1wqhfi" }],
    ["path", { d: "M21 13v1a4 4 0 0 1-4 4H3", key: "1rx37r" }]
  ]
};
Yt.node;
const Vt = P(Yt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ut = {
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
Ut.node;
const Hn = P(Ut);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Jt = {
  name: "users",
  size: 24,
  node: [
    ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
    ["path", { d: "M16 3.128a4 4 0 0 1 0 7.744", key: "16gr8j" }],
    ["path", { d: "M22 21v-2a4 4 0 0 0-3-3.87", key: "kshegd" }],
    ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }]
  ]
};
Jt.node;
const Gt = P(Jt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Kt = {
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
Kt.node;
const Xt = P(Kt), k = "seal_hrms.my_desk.api.", v = {
  home: `${k}home`,
  leaveList: `${k}leave_list`,
  leaveOptions: `${k}leave_options`,
  leaveRecord: `${k}leave_record`,
  applyForLeave: `${k}apply_for_leave`,
  colleagues: `${k}colleagues`,
  cover: `${k}cover`,
  handoverRecord: `${k}handover_record`,
  toilList: `${k}toil_list`,
  toilRecord: `${k}toil_record`,
  saveToilClaim: `${k}save_toil_claim`,
  toilAction: `${k}toil_action`,
  timesheets: `${k}timesheets`,
  timesheetWeek: `${k}timesheet_week`,
  timesheetRecord: `${k}timesheet_record`,
  saveTimesheetWeek: `${k}save_timesheet_week`,
  timesheetClaim: `${k}timesheet_claim`,
  expenseList: `${k}expense_list`,
  expenseOptions: `${k}expense_options`,
  expenseRecord: `${k}expense_record`,
  claimExpenses: `${k}claim_expenses`,
  advanceList: `${k}advance_list`,
  advanceRecord: `${k}advance_record`,
  requestAdvance: `${k}request_advance`,
  payslips: `${k}payslips`,
  payslipRecord: `${k}payslip_record`,
  payslipPdf: `${k}payslip_pdf`,
  checkinStatus: `${k}checkin_status`,
  checkIn: `${k}check_in`,
  attendanceRequests: `${k}attendance_requests`,
  attendanceOptions: `${k}attendance_options`,
  attendanceRecord: `${k}attendance_record`,
  requestAttendance: `${k}request_attendance`,
  requestShift: `${k}request_shift`,
  myDetails: `${k}my_details`,
  updateMyContact: `${k}update_my_contact`,
  payoutOptions: `${k}payout_options`,
  requestPayoutChange: `${k}request_payout_change`,
  setPayoutEvidence: `${k}set_payout_evidence`,
  payoutRequestRecord: `${k}payout_request_record`,
  confirmScreen: `${k}confirm_screen`,
  travelList: `${k}travel_list`,
  travelOptions: `${k}travel_options`,
  travelRecord: `${k}travel_record`,
  requestTravel: `${k}request_travel`,
  travelAction: `${k}travel_action`,
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
function On(a) {
  return `/api/method/${v.payslipPdf}?name=${encodeURIComponent(a)}`;
}
function _e(a) {
  return a ? e("{0} will approve it.", [a]) : e("Nobody approves this yet. Ask HR to set your approver.");
}
function In(a, r) {
  return a === null ? _e(r) : r ? e("{0} days. {1} will approve it.", [String(a), r]) : e("{0} days. Nobody approves this yet. Ask HR to set your approver.", [String(a)]);
}
function N() {
  const a = ne();
  return Ae((r) => a.navigate(r), [a]);
}
const zn = mn(
  {
    Open: "info",
    Draft: "default",
    "Not Sent": "default",
    "Awaiting Acceptance": "warning",
    "Waiting for Authorisation": "warning",
    "Waiting for Approval": "warning",
    "Waiting for HR": "warning",
    "Pending Approval": "warning",
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
function jn(a) {
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
    case "Pending Approval":
      return e("Pending Approval");
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
function $({ value: a }) {
  return a ? /* @__PURE__ */ t(pn, { status: a, label: jn(a), toneOf: zn }) : null;
}
const Yn = 864e5;
function Zt(a) {
  const [r, n, o] = a.split("-").map(Number);
  return Date.UTC(r, n - 1, o);
}
function Vn(a) {
  return new Date(a).toISOString().slice(0, 10);
}
function ke(a, r) {
  return Vn(Zt(a) + r * Yn);
}
function et(a) {
  const r = (new Date(Zt(a)).getUTCDay() + 6) % 7;
  return ke(a, -r);
}
function J(a = /* @__PURE__ */ new Date()) {
  const r = (n) => String(n).padStart(2, "0");
  return `${a.getFullYear()}-${r(a.getMonth() + 1)}-${r(a.getDate())}`;
}
function Ke(a) {
  return Array.from({ length: 7 }, (r, n) => ke(a, n));
}
function xe(a) {
  const r = typeof a == "number" ? a : Number.parseFloat(String(a ?? ""));
  return Number.isFinite(r) && r > 0 ? Math.round(r * 100) / 100 : 0;
}
function Qt(a, r) {
  return Math.round(a.reduce((n, o) => n + xe(o.hours[r]), 0) * 100) / 100;
}
function Un(a) {
  return Math.round(Ke("2000-01-03").reduce((r, n, o) => r + Qt(a, o), 0) * 100) / 100;
}
function dt(a, r) {
  return { row: a.reduce((o, s) => Math.max(o, s.row), 0) + 1, activity_type: r, description: "", is_billable: 0, hours: [0, 0, 0, 0, 0, 0, 0] };
}
function Jn(a) {
  return a.map((r, n) => ({
    row: n + 1,
    activity_type: r.activity_type,
    project: r.project ?? null,
    task: r.task ?? null,
    description: r.description ?? "",
    is_billable: r.is_billable ? 1 : 0,
    hours: [0, 0, 0, 0, 0, 0, 0]
  }));
}
function Gn(a, r, n, o) {
  return a.map((s) => s.row === r ? { ...s, hours: s.hours.map((c, i) => xe(i === n ? o : c)) } : s);
}
function Kn(a) {
  return a.filter((r) => r.hours.some((n) => xe(n) > 0) || (r.description ?? "").trim()).map((r, n) => ({ ...r, row: n + 1, hours: Array.from({ length: 7 }, (o, s) => xe(r.hours[s])) }));
}
function Xn() {
  return "geolocation" in navigator ? new Promise(
    (a) => navigator.geolocation.getCurrentPosition(
      (r) => a({ latitude: r.coords.latitude, longitude: r.coords.longitude }),
      () => a(null),
      { enableHighAccuracy: !0, timeout: 1e4, maximumAge: 6e4 }
    )
  ) : Promise.resolve(null);
}
function Zn() {
  const a = N(), r = O(), { data: n, isLoading: o, error: s, mutate: c } = A(v.checkinStatus), i = W(v.checkIn), [d, y] = q(!1), [p, f] = q(!1), u = async () => {
    if (!n) return;
    f(!1);
    let h = null;
    n.location && (y(!0), h = await Xn(), y(!1), f(!h));
    try {
      await i.run({ log_type: n.next, ...h ?? {} }), r.success(n.next === "IN" ? e("Checked in.") : e("Checked out.")), await c();
    } catch {
    }
  };
  return /* @__PURE__ */ t(ae, { title: e("Check-in"), onBack: () => a(""), loading: o, error: s, onRetry: c, children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
    n.offered ? /* @__PURE__ */ m(de, { children: [
      i.errorMessage && /* @__PURE__ */ t(S, { tone: "error", children: i.errorMessage }),
      p && /* @__PURE__ */ t(S, { tone: "warning", children: e("Your phone did not share where you are. Allow location for this site if HR needs it.") }),
      /* @__PURE__ */ m(w, { size: "lg", loading: d || i.loading, onClick: u, children: [
        n.next === "IN" ? /* @__PURE__ */ t(Fn, {}) : /* @__PURE__ */ t(Bn, {}),
        n.next === "IN" ? e("Check In") : e("Check Out")
      ] }),
      n.location && /* @__PURE__ */ m(te, { size: "sm", muted: !0, children: [
        /* @__PURE__ */ t(Qe, { "aria-hidden": !0, className: "mr-1 inline size-4" }),
        e("Where you are is recorded with each check-in, as HR asks.")
      ] })
    ] }) : /* @__PURE__ */ t(S, { tone: "info", children: e("HR has not turned on checking in from the phone.") }),
    /* @__PURE__ */ t(B, { title: e("Today"), children: n.today.length === 0 ? /* @__PURE__ */ t(te, { muted: !0, children: e("No check-ins today yet. Clock-ins on the office device show here too.") }) : /* @__PURE__ */ t(T, { divided: !0, children: n.today.map((h) => /* @__PURE__ */ t(
      M,
      {
        primary: h.log_type === "IN" ? e("In") : e("Out"),
        secondary: h.device_id ? e("{0} · {1}", [Ce(h.time), h.device_id]) : Ce(h.time)
      },
      h.name
    )) }) })
  ] }) });
}
function Qn() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.attendanceRequests);
  return /* @__PURE__ */ t(
    oe,
    {
      title: e("Attendance Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.attendanceNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("New Request")
      ] }),
      children: c && !r?.attendance.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Qe, {}), title: e("No attendance requests"), description: e("Ask for days you worked from home or on duty elsewhere to count as attended.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r?.attendance ?? []).map((i) => /* @__PURE__ */ t(
        M,
        {
          primary: i.reason === "Work From Home" ? e("Work From Home") : e("On Duty"),
          secondary: e("{0} to {1}", [_(i.from_date), _(i.to_date)]),
          action: /* @__PURE__ */ t($, { value: i.docstatus === 1 ? "Approved" : i.docstatus === 2 ? "Cancelled" : "Open" }),
          onClick: () => a(l.attendanceRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function ea() {
  const a = N(), r = O(), n = W(v.requestAttendance), o = me(() => ee.object({ from_date: Re(() => e("From Date")), to_date: Re(() => e("To Date")), reason: le(() => e("Reason")) }).loose(), []), s = pe({
    schema: o,
    defaultValues: { from_date: J(), to_date: J(), reason: "Work From Home", explanation: "", half_day: !1 }
  }), c = s.watch("from_date");
  return /* @__PURE__ */ t(ae, { title: e("New Attendance Request"), onBack: () => a(l.attendance), children: /* @__PURE__ */ m(
    ye,
    {
      form: s,
      onSubmit: async (i) => {
        const d = await n.run({ ...i, half_day: i.half_day ? 1 : 0 });
        r.success(e("Request sent to HR.")), a(l.attendanceRecord(d));
      },
      children: [
        /* @__PURE__ */ t(
          gt,
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
        /* @__PURE__ */ t(he, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(he, { name: "to_date", label: e("To Date"), required: !0, minDate: c || void 0 }),
        /* @__PURE__ */ t(Ze, { name: "half_day", label: e("Half Day") }),
        /* @__PURE__ */ t(H, { name: "explanation", label: e("Explanation"), multiline: !0, rows: 3 }),
        /* @__PURE__ */ t(fe, { submitLabel: e("Send Request"), onCancel: () => a(l.attendance) })
      ]
    }
  ) });
}
function ut({ doctype: a }) {
  const r = N(), n = ie(Z().name), { data: o, isLoading: s, error: c, mutate: i } = A(v.attendanceRecord, { doctype: a, name: n }), d = a === "Shift Request";
  return /* @__PURE__ */ t(
    Q,
    {
      title: d ? e("Shift Request") : e("Attendance Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t($, { value: d ? o.status : o.docstatus === 1 ? "Approved" : "Open" }),
      onBack: () => r(d ? l.shifts : l.attendance),
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ t(
        U,
        {
          items: [
            { label: e("Shift Type"), value: o.shift_type ?? null, hideWhenEmpty: !0 },
            { label: e("Reason"), value: o.reason ?? null, hideWhenEmpty: !0 },
            { label: e("From Date"), value: _(o.from_date) },
            { label: e("To Date"), value: o.to_date ? _(o.to_date) : null, hideWhenEmpty: !0 },
            { label: e("Approver"), value: o.approver_name, hideWhenEmpty: !0 },
            { label: e("Explanation"), value: o.explanation ?? null, hideWhenEmpty: !0, full: !0 }
          ]
        }
      )
    }
  );
}
function ta() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.attendanceRequests);
  return /* @__PURE__ */ t(
    oe,
    {
      title: e("Shift Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.shiftNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("New Request")
      ] }),
      children: c && !r?.shifts.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Vt, {}), title: e("No shift requests"), description: e("Ask to work a different shift for some days.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r?.shifts ?? []).map((i) => /* @__PURE__ */ t(
        M,
        {
          primary: i.shift_type,
          secondary: i.to_date ? e("{0} to {1}", [_(i.from_date), _(i.to_date)]) : e("From {0}", [_(i.from_date)]),
          action: /* @__PURE__ */ t($, { value: i.status }),
          onClick: () => a(l.shiftRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function na() {
  const a = N(), r = O(), n = A(v.attendanceOptions), o = W(v.requestShift), s = me(() => ee.object({ shift_type: le(() => e("Shift Type")), from_date: Re(() => e("From Date")) }).loose(), []), c = pe({ schema: s, defaultValues: { shift_type: "", from_date: J(), to_date: "" } });
  return /* @__PURE__ */ m(ae, { title: e("New Shift Request"), onBack: () => a(l.shifts), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    n.data && /* @__PURE__ */ t(S, { tone: n.data.has_shift_approver ? "info" : "warning", children: _e(n.data.has_shift_approver ? n.data.shift_approver_name : null) }),
    /* @__PURE__ */ m(
      ye,
      {
        form: c,
        onSubmit: async (i) => {
          const d = await o.run({ shift_type: i.shift_type, from_date: i.from_date, to_date: i.to_date || void 0 });
          r.success(e("Request sent to {0}.", [n.data?.shift_approver_name ?? e("your shift approver")])), a(l.shiftRecord(d));
        },
        children: [
          /* @__PURE__ */ t(se, { name: "shift_type", label: e("Shift Type"), required: !0, options: (n.data?.shift_types ?? []).map((i) => ({ value: i, label: i })) }),
          /* @__PURE__ */ t(he, { name: "from_date", label: e("From Date"), required: !0 }),
          /* @__PURE__ */ t(he, { name: "to_date", label: e("To Date"), hint: e("Leave empty if the shift carries on.") }),
          /* @__PURE__ */ t(fe, { submitLabel: e("Send Request"), onCancel: () => a(l.shifts) })
        ]
      }
    )
  ] });
}
function He(a, r, n) {
  return /* @__PURE__ */ t(T, { divided: !0, children: a.map((o) => /* @__PURE__ */ t(
    M,
    {
      primary: r ? e("Covered by {0}", [o.stand_in]) : o.employee_name,
      secondary: e("{0} to {1}", [_(o.leave_from), _(o.leave_to)]),
      action: /* @__PURE__ */ t($, { value: o.waiting_for_me ? "Pending" : o.status }),
      onClick: () => n(l.handover(o.name))
    },
    o.name
  )) });
}
function aa() {
  const a = N(), [r, n] = q("to_answer"), { data: o, isLoading: s, error: c, mutate: i, hasLoaded: d } = A(v.cover), y = (p, f) => /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Gt, {}), title: p, description: f });
  return /* @__PURE__ */ m(oe, { title: e("Cover"), onBack: () => a(""), loading: s, error: c, onRetry: i, children: [
    /* @__PURE__ */ t(
      yn,
      {
        label: e("Handovers"),
        value: r,
        onChange: n,
        items: [
          { id: "to_answer", label: e("To Answer"), count: o?.to_answer.filter((p) => p.waiting_for_me).length },
          { id: "covering", label: e("Covering"), count: o?.covering.length },
          { id: "mine", label: e("Mine"), count: o?.mine.length }
        ]
      }
    ),
    /* @__PURE__ */ t(Pe, { id: "to_answer", value: r, children: d && !o?.to_answer.length ? y(e("Nobody has asked you to cover"), e("When a colleague names you as their stand-in, it shows here for you to agree or decline.")) : He(o?.to_answer ?? [], !1, a) }),
    /* @__PURE__ */ t(Pe, { id: "covering", value: r, children: d && !o?.covering.length ? y(e("You are not covering anyone now"), e("Work you agreed to cover shows here while the person is away.")) : He(o?.covering ?? [], !1, a) }),
    /* @__PURE__ */ t(Pe, { id: "mine", value: r, children: d && !o?.mine.length ? y(e("No handovers of your own"), e("When you apply for leave, the handover you send shows here.")) : He(o?.mine ?? [], !0, a) })
  ] });
}
function oa() {
  const a = N(), r = O(), n = ie(Z().name), { data: o, isLoading: s, error: c, mutate: i } = A(v.handoverRecord, { name: n }), d = W(v.respond), y = W(v.respondAuthority), p = W(v.addNote), f = W(v.returnNote), u = W(v.returnWork), [h, g] = q(null), [x, E] = q(""), [D, L] = q(!1), [I, V] = q(!1), [z, G] = q(null), j = async (C, $e) => {
    V(!0), G(null);
    try {
      await C(), r.success($e), g(null), E(""), await i();
    } catch (ce) {
      G(ce);
    } finally {
      V(!1);
    }
  }, b = o && o.can_answer ? /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(w, { variant: "outline", onClick: () => g({ kind: "decline" }), children: e("Decline") }),
    /* @__PURE__ */ t(w, { loading: I, onClick: () => j(() => d.run({ name: n, answer: "Accepted" }), e("You agreed to cover this.")), children: e("Accept") })
  ] }) : o && o.can_return ? /* @__PURE__ */ t(w, { onClick: () => L(!0), children: e("I'm Back") }) : void 0;
  return /* @__PURE__ */ m(
    Q,
    {
      title: o ? o.is_owner ? e("My Handover") : e("Cover for {0}", [o.employee_name]) : e("Handover"),
      subtitle: o && e("{0} to {1}", [_(o.leave_from), _(o.leave_to)]),
      meta: o && /* @__PURE__ */ t($, { value: o.status }),
      onBack: () => a(l.cover),
      actions: b,
      loading: s,
      error: c,
      onRetry: i,
      children: [
        o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
          z ? /* @__PURE__ */ t(S, { tone: "error", children: d.errorMessage || y.errorMessage || u.errorMessage || e("That did not go through. Try again.") }) : null,
          /* @__PURE__ */ t(
            U,
            {
              items: [
                { label: e("Stand-in"), value: o.stand_in },
                { label: e("Back On"), value: o.return_date ? _(o.return_date) : null, hideWhenEmpty: !0 },
                { label: e("Decline Reason"), value: o.decline_reason, hideWhenEmpty: !0, full: !0 },
                { label: e("Handover Notes"), value: o.notes, hideWhenEmpty: !0, full: !0 },
                { label: e("Return Note"), value: o.return_note, hideWhenEmpty: !0, full: !0 }
              ]
            }
          ),
          /* @__PURE__ */ t(B, { title: e("Work"), children: o.work.length === 0 ? /* @__PURE__ */ t(te, { muted: !0, children: e("No work items were handed over; the notes say what to look after.") }) : /* @__PURE__ */ t(T, { divided: !0, children: o.work.map((C) => /* @__PURE__ */ t(
            M,
            {
              primary: C.description,
              secondary: [C.covered_by, C.due_date ? e("Due {0}", [_(C.due_date)]) : "", C.notes ?? ""].filter(Boolean).join(" · "),
              action: C.mine && o.status === "Active" ? /* @__PURE__ */ t(w, { variant: "ghost", onClick: () => g({ kind: "note", row: C.row, text: C.notes ?? "" }), children: e("Leave a Note") }) : C.progress || C.acceptance ? /* @__PURE__ */ t($, { value: C.progress || C.acceptance }) : void 0
            },
            C.row
          )) }) }),
          o.approvals.length > 0 && /* @__PURE__ */ t(B, { title: e("Approvals"), children: /* @__PURE__ */ t(T, { divided: !0, children: o.approvals.map((C) => /* @__PURE__ */ t(
            M,
            {
              primary: C.label,
              secondary: C.covered_by,
              action: C.mine && o.can_answer && C.acceptance === "Pending" ? /* @__PURE__ */ m("div", { className: "flex gap-1", children: [
                /* @__PURE__ */ t(w, { variant: "ghost", onClick: () => g({ kind: "decline-approval", row: C.row }), children: e("Decline") }),
                /* @__PURE__ */ t(
                  w,
                  {
                    variant: "ghost",
                    onClick: () => j(() => y.run({ name: n, row: C.row, answer: "Accepted" }), e("You agreed to approve in their place.")),
                    children: e("Accept")
                  }
                )
              ] }) : C.acceptance ? /* @__PURE__ */ t($, { value: C.acceptance }) : void 0
            },
            C.row
          )) }) }),
          o.is_stand_in && o.status === "Active" && /* @__PURE__ */ t(w, { variant: "outline", onClick: () => g({ kind: "return-note" }), children: e("Note for Return") })
        ] }),
        /* @__PURE__ */ t(
          wt,
          {
            open: !!h,
            onClose: () => g(null),
            title: h?.kind === "note" ? e("Leave a Note") : h?.kind === "return-note" ? e("Note for Return") : e("Decline"),
            description: h?.kind === "note" ? e("What you did on this piece of work, for when they are back.") : h?.kind === "return-note" ? e("What they should know on their first day back.") : e("Say why you cannot cover it, so they can ask someone else."),
            actions: /* @__PURE__ */ m(de, { children: [
              /* @__PURE__ */ t(w, { variant: "outline", onClick: () => g(null), children: e("Cancel") }),
              /* @__PURE__ */ t(
                w,
                {
                  loading: I,
                  disabled: !(h?.kind === "note" ? h.text : x).trim(),
                  onClick: () => {
                    h && (h.kind === "decline" ? j(() => d.run({ name: n, answer: "Declined", reason: x }), e("You declined.")) : h.kind === "decline-approval" ? j(() => y.run({ name: n, row: h.row, answer: "Declined", reason: x }), e("You declined.")) : h.kind === "note" ? j(() => p.run({ name: n, row: h.row, note: h.text }), e("Note saved.")) : j(() => f.run({ name: n, note: x }), e("Note saved.")));
                  },
                  children: h?.kind === "decline" || h?.kind === "decline-approval" ? e("Decline") : e("Save Note")
                }
              )
            ] }),
            children: /* @__PURE__ */ t(
              fn,
              {
                "aria-label": e("Note"),
                rows: 4,
                value: h?.kind === "note" ? h.text : x,
                onChange: (C) => h?.kind === "note" ? g({ ...h, text: C.target.value }) : E(C.target.value)
              }
            )
          }
        ),
        /* @__PURE__ */ t(
          bt,
          {
            open: D,
            onClose: () => L(!1),
            title: e("Take your work back now?"),
            confirmLabel: e("I'm Back"),
            onConfirm: async () => {
              await u.run({ name: n }), r.success(e("Your work is back with you.")), await i();
            },
            children: e("Everything your stand-in was covering comes back to you, and they stop approving in your place.")
          }
        )
      ]
    }
  );
}
function ra() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s } = A(v.home), c = l.week(et(J())), i = [
    { label: e("Leave"), hint: e("Apply, and see what you asked for"), path: l.leave, icon: /* @__PURE__ */ t(Ve, {}) },
    { label: e("Cover"), hint: e("Handovers to answer and work you cover"), path: l.cover, icon: /* @__PURE__ */ t(Gt, {}) },
    { label: e("Time Off in Lieu"), hint: e("Claim extra hours as time off"), path: l.toil, icon: /* @__PURE__ */ t(Je, {}) },
    { label: e("Timesheets"), hint: e("Your week, day by day"), path: l.timesheet, icon: /* @__PURE__ */ t(Ue, {}) },
    { label: e("Expense Claims"), hint: e("Claims and receipts"), path: l.expenses, icon: /* @__PURE__ */ t(Ge, {}) },
    { label: e("Advances"), hint: e("Money paid ahead and what is left to settle"), path: l.advances, icon: /* @__PURE__ */ t($t, {}) },
    { label: e("Payslips"), hint: e("Your pay, month by month"), path: l.pay, icon: /* @__PURE__ */ t(Xt, {}) },
    { label: e("Attendance Requests"), hint: e("Days worked away from the office"), path: l.attendance, icon: /* @__PURE__ */ t(Qe, {}) },
    { label: e("Shift Requests"), hint: e("Ask to work another shift"), path: l.shifts, icon: /* @__PURE__ */ t(Vt, {}) },
    { label: e("Travel Requests"), hint: e("Trips for work, approved by your line manager"), path: l.travel, icon: /* @__PURE__ */ t(It, {}) },
    { label: e("My Details"), hint: e("Contact, dependants and where you are paid"), path: l.me, icon: /* @__PURE__ */ t(Pn, {}) }
  ];
  return r?.checkin.offered && i.splice(4, 0, { label: e("Check-in"), hint: e("Check in and out from your phone"), path: l.checkIn, icon: /* @__PURE__ */ t(ct, {}) }), /* @__PURE__ */ t(vn, { title: e("Self Service"), subtitle: r?.employee.employee_name, loading: n, error: o, onRetry: s, children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
    r && r.balances.length > 0 && /* @__PURE__ */ t(Ct, { columns: 2, children: r.balances.map((d) => /* @__PURE__ */ t(ze, { label: d.label, value: e("{0} days", [String(d.value)]), onClick: () => a(d.key.startsWith("toil") ? l.toil : l.leave) }, d.key)) }),
    /* @__PURE__ */ t(B, { title: e("Quick Actions"), children: /* @__PURE__ */ m("div", { className: "grid grid-cols-1 gap-2 sm:grid-cols-2", children: [
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.leaveNew), children: [
        /* @__PURE__ */ t(Ve, {}),
        e("Apply for Leave")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.toilNew), children: [
        /* @__PURE__ */ t(Je, {}),
        e("Claim Time Off")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(c), children: [
        /* @__PURE__ */ t(En, {}),
        e("This Week's Timesheet")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.expenseNew), children: [
        /* @__PURE__ */ t(Ge, {}),
        e("New Expense Claim")
      ] }),
      r?.checkin.offered && /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.checkIn), children: [
        /* @__PURE__ */ t(ct, {}),
        e("Check In")
      ] })
    ] }) }),
    r && r.in_flight.length > 0 && /* @__PURE__ */ t(B, { title: e("In Progress"), children: /* @__PURE__ */ t(T, { divided: !0, children: r.in_flight.map((d) => {
      const y = bn(d.doctype);
      return /* @__PURE__ */ t(M, { primary: d.label, action: /* @__PURE__ */ t(we, { children: d.count }), onClick: y ? () => a(y) : void 0 }, d.key);
    }) }) }),
    /* @__PURE__ */ t(B, { title: e("Everything in Self Service"), children: /* @__PURE__ */ t(T, { divided: !0, children: i.map((d) => /* @__PURE__ */ t(M, { primary: d.label, secondary: d.hint, icon: d.icon, action: /* @__PURE__ */ t(St, { "aria-hidden": !0 }), onClick: () => a(d.path) }, d.path)) }) })
  ] }) });
}
const ia = "seal-draft:", sa = 30, la = 400;
function ca(a, r, n) {
  return `${ia}${a}:${r}:${n}`;
}
function tt() {
  try {
    return typeof window < "u" ? window.localStorage : null;
  } catch {
    return null;
  }
}
function Xe(a, r = Date.now()) {
  const n = tt();
  if (!n) return null;
  try {
    const o = n.getItem(a);
    if (!o) return null;
    const s = JSON.parse(o);
    if (!s || typeof s.saved != "number" || !("value" in s)) throw new Error("not a draft");
    return r - s.saved > sa * 864e5 ? (n.removeItem(a), null) : { value: s.value, saved: s.saved };
  } catch {
    try {
      n.removeItem(a);
    } catch {
    }
    return null;
  }
}
function da(a, r, n = Date.now()) {
  const o = tt();
  if (!o) return !1;
  try {
    return o.setItem(a, JSON.stringify({ saved: n, value: r })), !0;
  } catch {
    return !1;
  }
}
function en(a) {
  try {
    tt()?.removeItem(a);
  } catch {
  }
}
function Me(a, r, n) {
  const o = a && n ? ca(a, r, n) : null, [s, c] = q(() => o ? Xe(o) : null), i = be(null), d = be(o);
  ue(() => {
    d.current !== o && (d.current = o, c(o ? Xe(o) : null));
  }, [o]), ue(
    () => () => {
      i.current && clearTimeout(i.current);
    },
    []
  );
  const y = Ae(
    (u) => {
      o && (i.current && clearTimeout(i.current), i.current = setTimeout(() => da(o, u), la));
    },
    [o]
  ), p = Ae(() => {
    i.current && clearTimeout(i.current), i.current = null, o && en(o), c(null);
  }, [o]), f = Ae(() => c(null), []);
  return { key: o, restored: s, keep: y, clear: p, dismiss: f };
}
function qe(a) {
  return J(new Date(a));
}
function ua(a) {
  return { show: !!a?.needed, standInRequired: !!a?.needed && !!a?.required };
}
function ha(a, r) {
  const n = a.filter((c) => c.work_date), o = new Set(n.map((c) => c.work_date)), s = r.filter((c) => !o.has(c.work_date)).map((c) => ({ work_date: c.work_date, hours: c.hours, work_done: "" }));
  return [...n, ...s].sort((c, i) => c.work_date.localeCompare(i.work_date));
}
function ma(a) {
  if (a.change === "Mobile Money") return a.mobile_no?.trim() ? [] : ["mobile_no"];
  const r = ["bank", "bank_account_no", "account_name"].filter((n) => !a[n]?.trim());
  return a.evidence ? r : [...r, "evidence"];
}
function pa(a, r) {
  return {
    itinerary: a.filter((n) => n.travel_from.trim() || n.travel_to.trim()),
    costings: r.filter((n) => n.expense_type || (n.total_amount ?? 0) > 0)
  };
}
function ya() {
  const a = N(), [r, n] = q("all"), { data: o, isLoading: s, error: c, mutate: i, hasLoaded: d } = A(v.leaveList), y = o ?? [], p = y.filter((u) => u.status === "Open" && u.docstatus === 0), f = r === "open" ? p : r === "decided" ? y.filter((u) => !p.includes(u)) : y;
  return /* @__PURE__ */ t(
    oe,
    {
      title: e("Leave"),
      onBack: () => a(""),
      loading: s,
      error: c,
      onRetry: i,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.leaveNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("Apply for Leave")
      ] }),
      toolbar: /* @__PURE__ */ t(
        gn,
        {
          label: e("Show"),
          value: r,
          onChange: n,
          options: [
            { value: "all", label: e("All"), count: y.length },
            { value: "open", label: e("Waiting"), count: p.length },
            { value: "decided", label: e("Decided"), count: y.length - p.length }
          ]
        }
      ),
      children: d && f.length === 0 ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Ve, {}), title: e("No leave here"), description: e("Leave you apply for shows here until it is decided, and after.") }) : /* @__PURE__ */ t(T, { divided: !0, children: f.map((u) => /* @__PURE__ */ t(
        M,
        {
          primary: u.leave_type,
          secondary: u.handover ? e("{0} to {1} · {2} days · covered by {3}", [_(u.from_date), _(u.to_date), String(u.total_leave_days), u.handover.stand_in]) : e("{0} to {1} · {2} days", [_(u.from_date), _(u.to_date), String(u.total_leave_days)]),
          action: /* @__PURE__ */ t($, { value: u.status }),
          onClick: () => a(l.leaveRecord(u.name))
        },
        u.name
      )) })
    }
  );
}
function fa() {
  const a = N(), r = O(), [n] = ft(), o = me(
    () => ee.object({
      leave_type: le(() => e("Leave Type")),
      from_date: Re(() => e("From Date")),
      to_date: Re(() => e("To Date"))
    }),
    []
  ), s = () => ({ leave_type: n.get("type") ?? "", from_date: "", to_date: "", half_day: !1, description: "", stand_in: "", handover_notes: "", todos: [], approvals: [] }), c = pe({ schema: o.passthrough(), defaultValues: s() }), i = Me(ne().user, "leave-application", "new"), [d, y] = q(null);
  ue(() => {
    i.restored?.value && !n.get("type") && (c.reset({ ...s(), ...i.restored.value }), y(i.restored.saved)), i.dismiss();
    const b = c.watch((C) => i.keep({ ...s(), ...C }));
    return () => b.unsubscribe();
  }, []);
  const p = () => {
    i.clear(), y(null), c.reset(s());
  }, [f, u, h, g] = c.watch(["leave_type", "from_date", "to_date", "half_day"]), x = !!(f && u && h), E = A(v.leaveOptions), D = A(v.leaveOptions, { leave_type: f, from_date: u, to_date: h, half_day: g ? 1 : 0 }, { enabled: x }), L = { ...D, data: x ? D.data : void 0 }, I = A(v.colleagues, {}, { enabled: !!L.data?.handover.needed }), V = W(v.applyForLeave), z = ua(x ? L.data?.handover : void 0), G = (L.data ?? E.data)?.leave_types.find((b) => b.name === f), j = async (b) => {
    if (z.standInRequired && !b.stand_in) return { errors: { stand_in: e("Your company asks for cover on this leave. Choose who will cover your work.") } };
    const C = await V.run({
      leave_type: b.leave_type,
      from_date: b.from_date,
      to_date: b.to_date,
      half_day: b.half_day ? 1 : 0,
      description: b.description,
      stand_in: z.show && b.stand_in || void 0,
      handover_notes: b.handover_notes,
      todos: JSON.stringify(b.todos),
      approvals: JSON.stringify(b.approvals)
    });
    i.clear(), r.success(C.handover ? e("Leave applied for, and the handover sent to your stand-in.") : e("Leave applied for.")), a(l.leaveRecord(C.name));
  };
  return /* @__PURE__ */ m(ae, { title: e("Apply for Leave"), onBack: () => a(l.leave), loading: E.isLoading && !E.data, error: E.error, onRetry: E.mutate, children: [
    d !== null && /* @__PURE__ */ t(S, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: p, children: e("Start Again") }), children: e("You started this application on {0} and had not sent it.", [_(qe(d))]) }),
    /* @__PURE__ */ m(ye, { form: c, onSubmit: j, children: [
      /* @__PURE__ */ t(st, { title: e("Leave"), children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          se,
          {
            name: "leave_type",
            label: e("Leave Type"),
            required: !0,
            options: (E.data?.leave_types ?? []).map((b) => ({
              value: b.name,
              label: b.name,
              description: b.left === null ? e("Unpaid") : e("{0} days left", [String(b.left)])
            })),
            hint: G && G.left !== null ? e("{0} days left", [String(G.left)]) : void 0
          }
        ),
        /* @__PURE__ */ t(he, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(he, { name: "to_date", label: e("To Date"), required: !0, minDate: u || void 0 }),
        /* @__PURE__ */ t(Ze, { name: "half_day", label: e("Half Day"), hint: e("Only the first day is a half day.") }),
        /* @__PURE__ */ t(H, { name: "description", label: e("Reason"), multiline: !0, rows: 3 }),
        x && L.data && /* @__PURE__ */ t(S, { tone: "info", children: In(L.data.days, L.data.approver_name) })
      ] }) }),
      z.show && /* @__PURE__ */ t(
        st,
        {
          title: e("Handover"),
          description: z.standInRequired ? e("Your company asks for cover on leave like this. Your stand-in is asked to agree before the leave is approved.") : e("Your company suggests arranging cover. You can leave this out."),
          children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
            /* @__PURE__ */ t(
              Ee,
              {
                name: "stand_in",
                label: e("Stand-in"),
                required: z.standInRequired,
                options: (I.data ?? []).map((b) => ({ value: b.name, label: b.employee_name })),
                hint: e("A colleague in your company who is not away at the same time.")
              }
            ),
            /* @__PURE__ */ t(H, { name: "handover_notes", label: e("Handover Notes"), multiline: !0, rows: 4, hint: e("What your stand-in needs to know.") }),
            (L.data?.work.length ?? 0) > 0 && /* @__PURE__ */ t(
              Ee,
              {
                name: "todos",
                multiple: !0,
                label: e("Work to Hand Over"),
                options: (L.data?.work ?? []).map((b) => ({ value: b.todo, label: b.description, description: b.due_date ? e("Due {0}", [_(b.due_date)]) : void 0 })),
                hint: e("Open items on your work list. Your stand-in gets them while you are away.")
              }
            ),
            (L.data?.approvals.length ?? 0) > 0 && /* @__PURE__ */ t(
              Ee,
              {
                name: "approvals",
                multiple: !0,
                label: e("Approvals to Hand Over"),
                options: (L.data?.approvals ?? []).map((b) => ({ value: b.authority, label: b.authority_label })),
                hint: e("Your stand-in approves these in your place, once they agree.")
              }
            )
          ] })
        }
      ),
      /* @__PURE__ */ t(fe, { submitLabel: e("Apply"), onCancel: () => a(l.leave) })
    ] })
  ] });
}
function va() {
  const a = N(), r = ie(Z().name), { data: n, isLoading: o, error: s, mutate: c } = A(v.leaveRecord, { name: r });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n ? n.leave_type : e("Leave"),
      subtitle: n && !n.mine ? n.employee_name : r,
      meta: n && /* @__PURE__ */ t($, { value: n.status }),
      onBack: () => a(l.leave),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          U,
          {
            items: [
              { label: e("From Date"), value: _(n.from_date) },
              { label: e("To Date"), value: _(n.to_date) },
              { label: e("Days"), value: String(n.total_leave_days) },
              { label: e("Half Day"), value: n.half_day ? e("Yes") : e("No") },
              { label: e("Leave Approver"), value: n.leave_approver_name, hideWhenEmpty: !0 },
              { label: e("Applied On"), value: _(n.posting_date) },
              { label: e("Reason"), value: n.description, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        n.handover ? /* @__PURE__ */ t(T, { divided: !0, children: /* @__PURE__ */ t(
          M,
          {
            primary: e("Handover to {0}", [n.handover.stand_in]),
            action: /* @__PURE__ */ t($, { value: n.handover.status }),
            onClick: () => a(l.handover(n.handover.name))
          }
        ) }) : /* @__PURE__ */ t(te, { muted: !0, children: e("No handover for this leave.") })
      ] })
    }
  );
}
class nt extends Error {
  constructor() {
    super(...arguments);
    it(this, "name", "VerificationCancelled");
  }
}
function Le(a, r = 0) {
  if (!a || typeof a != "object" || r > 3) return !1;
  const n = a;
  return n.exc_type === "VerificationNeeded" || typeof n.exception == "string" && n.exception.includes("VerificationNeeded") ? !0 : Le(n.payload, r + 1) || Le(n.original, r + 1);
}
async function at(a, r) {
  try {
    return await a();
  } catch (n) {
    if (!Le(n)) throw n;
    if (!await r()) throw new nt();
    return a();
  }
}
function ot(a, r) {
  const n = ne(), o = Le(a), [s, c] = q(!1), i = be(!1), d = async () => {
    c(!0);
    try {
      await n.verify() && await r();
    } finally {
      c(!1);
    }
  };
  return ue(() => {
    o && !i.current && (i.current = !0, d());
  }, [o]), { needed: o, busy: s, confirm: d, error: o ? void 0 : a };
}
function We({ what: a, busy: r, onConfirm: n }) {
  return /* @__PURE__ */ t(
    S,
    {
      tone: "info",
      role: "status",
      title: e("Confirm It Is You"),
      action: /* @__PURE__ */ t(w, { loading: r, onClick: n, children: e("Confirm") }),
      children: a
    }
  );
}
function ga() {
  const a = N(), r = O(), { data: n, isLoading: o, error: s, mutate: c } = A(v.myDetails), i = W(v.updateMyContact), [d, y] = q(!1), [p, f] = q("");
  return /* @__PURE__ */ m(Q, { title: e("My Details"), subtitle: n?.employee.employee_name, onBack: () => a(""), loading: o, error: s, onRetry: c, children: [
    n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
      /* @__PURE__ */ t(
        U,
        {
          items: [
            { label: e("Employee ID"), value: n.employee.name },
            { label: e("Designation"), value: n.employee.designation, hideWhenEmpty: !0 },
            { label: e("Department"), value: n.employee.department, hideWhenEmpty: !0 },
            { label: e("Company"), value: n.employee.company },
            { label: e("Date of Joining"), value: n.employee.date_of_joining ? _(n.employee.date_of_joining) : null, hideWhenEmpty: !0 },
            { label: e("Company Email"), value: n.employee.company_email, hideWhenEmpty: !0 },
            { label: e("Personal Email"), value: n.employee.personal_email, hideWhenEmpty: !0 }
          ]
        }
      ),
      /* @__PURE__ */ m(
        B,
        {
          title: e("Contact"),
          action: n.has_contact ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => y(!0), children: e("Change Mobile Number") }) : void 0,
          children: [
            /* @__PURE__ */ t(U, { items: [{ label: e("Mobile No."), value: n.mobile_no ?? e("None yet") }] }),
            !n.has_contact && /* @__PURE__ */ t(te, { muted: !0, children: e("HR has not linked a contact to your record yet; ask them to.") })
          ]
        }
      ),
      /* @__PURE__ */ t(B, { title: e("Dependants and Beneficiaries"), children: n.dependants.length === 0 ? /* @__PURE__ */ t(te, { muted: !0, children: e("None recorded. HR records dependants and beneficiaries.") }) : /* @__PURE__ */ t(T, { divided: !0, children: n.dependants.map((u) => /* @__PURE__ */ t(M, { primary: u.full_name, secondary: [u.relationship, u.type, u.dob ? _(u.dob) : ""].filter(Boolean).join(" · ") }, u.name)) }) }),
      /* @__PURE__ */ m(
        B,
        {
          title: e("Payout Details"),
          subtitle: e("Where your pay goes. Only the last four digits are shown."),
          action: /* @__PURE__ */ t(w, { disabled: !!n.payout_request, onClick: () => a(l.payoutNew), children: e("Request a Change") }),
          children: [
            n.payout ? /* @__PURE__ */ t(
              U,
              {
                items: [
                  { label: e("Bank"), value: n.payout.bank ?? e("None") },
                  { label: e("Account No."), value: n.payout.account_no, hideWhenEmpty: !0 },
                  { label: e("Account Name"), value: n.payout.account_name, hideWhenEmpty: !0 },
                  { label: e("Mobile Money"), value: n.payout.mobile_no ?? e("None") }
                ]
              }
            ) : /* @__PURE__ */ t(_a, { onConfirmed: c }),
            n.payout_requests.length > 0 && /* @__PURE__ */ t(T, { divided: !0, children: n.payout_requests.map((u) => /* @__PURE__ */ t(
              M,
              {
                primary: u.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
                secondary: Ce(u.creation),
                action: /* @__PURE__ */ t($, { value: u.status }),
                onClick: () => a(l.payoutRecord(u.name))
              },
              u.name
            )) })
          ]
        }
      )
    ] }),
    /* @__PURE__ */ t(
      wt,
      {
        open: d,
        onClose: () => y(!1),
        title: e("Change Mobile Number"),
        description: e("Your contact number at work. Where your pay goes changes only by a request to HR."),
        actions: /* @__PURE__ */ m(de, { children: [
          /* @__PURE__ */ t(w, { variant: "outline", onClick: () => y(!1), children: e("Cancel") }),
          /* @__PURE__ */ t(
            w,
            {
              loading: i.loading,
              disabled: !p.trim(),
              onClick: async () => {
                try {
                  await i.run({ mobile_no: p }), r.success(e("Mobile number changed.")), y(!1), f(""), await c();
                } catch {
                }
              },
              children: e("Save")
            }
          )
        ] }),
        children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-2", children: [
          i.errorMessage && /* @__PURE__ */ t(S, { tone: "error", children: i.errorMessage }),
          /* @__PURE__ */ t(Ne, { htmlFor: "new-mobile", children: e("New Mobile No.") }),
          /* @__PURE__ */ t(je, { id: "new-mobile", type: "tel", inputMode: "tel", autoComplete: "tel", value: p, onChange: (u) => f(u.target.value) })
        ] })
      }
    )
  ] });
}
function _a({ onConfirmed: a }) {
  const r = ne(), [n, o] = q(!1), s = async () => {
    o(!0);
    try {
      await r.verify() && await a();
    } finally {
      o(!1);
    }
  };
  return /* @__PURE__ */ t(We, { what: e("Your payout details show once you confirm it is you."), busy: n, onConfirm: s });
}
function ka() {
  const a = N(), r = ne(), n = O(), o = A(v.payoutOptions), s = W(v.requestPayoutChange), c = W(v.setPayoutEvidence), i = W(v.sendPayoutChange), d = pe({
    defaultValues: { change: "Bank Account", bank: "", bank_account_no: "", branch_code: "", account_name: "", mobile_no: "", evidence: null, reason: "" }
  }), y = d.watch("change"), p = me(
    () => ({ bank: e("Bank"), bank_account_no: e("Account No."), account_name: e("Account Name"), mobile_no: e("Mobile No."), evidence: e("Evidence") }),
    []
  ), f = async (u) => {
    const h = ma(u);
    if (h.length) return { errors: Object.fromEntries(h.map((x) => [x, e("{0} is needed.", [p[x]])])) };
    const g = await s.run({
      change: u.change,
      bank: u.change === "Bank Account" ? u.bank : void 0,
      bank_account_no: u.change === "Bank Account" ? u.bank_account_no : void 0,
      branch_code: u.change === "Bank Account" ? u.branch_code : void 0,
      account_name: u.change === "Bank Account" ? u.account_name : void 0,
      mobile_no: u.change === "Mobile Money" ? u.mobile_no : void 0,
      reason: u.reason
    });
    if (u.change === "Bank Account" && u.evidence) {
      const x = await vt(u.evidence, { doctype: "Payout Change Request", docname: g, fieldname: "evidence", isPrivate: !0 });
      await c.run({ name: g, file_url: x.file_url });
    }
    try {
      await at(() => i.run({ name: g }), r.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it."));
    } catch (x) {
      if (!(x instanceof nt)) throw x;
      n.info(e("Saved, not sent. Open it from My Details to send it."));
    }
    a(l.payoutRecord(g));
  };
  return /* @__PURE__ */ m(ae, { title: e("Request a Change"), subtitle: e("Where your pay goes"), onBack: () => a(l.me), loading: o.isLoading, error: o.error, onRetry: o.mutate, children: [
    /* @__PURE__ */ t(S, { tone: "info", children: e("HR confirms every change before any pay goes there. We also tell your current number and email, in case this was not you.") }),
    /* @__PURE__ */ m(ye, { form: d, onSubmit: f, children: [
      /* @__PURE__ */ t(
        gt,
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
      y === "Bank Account" ? /* @__PURE__ */ m(de, { children: [
        /* @__PURE__ */ t(se, { name: "bank", label: e("Bank"), required: !0, options: (o.data?.banks ?? []).map((u) => ({ value: u, label: u })) }),
        /* @__PURE__ */ t(H, { name: "bank_account_no", label: e("Account No."), required: !0 }),
        /* @__PURE__ */ t(H, { name: "branch_code", label: e("Branch") }),
        /* @__PURE__ */ t(H, { name: "account_name", label: e("Account Name"), required: !0, hint: e("As the bank has it. It must be in your own name.") }),
        /* @__PURE__ */ t(_t, { name: "evidence", label: e("Evidence"), required: !0, upload: !1, accept: "image/*,application/pdf", hint: e("A bank letter or the top of a statement, showing the account in your name.") })
      ] }) : /* @__PURE__ */ t(hn, { name: "mobile_no", label: e("Mobile No."), required: !0, hint: e("The number your pay should go to by mobile money.") }),
      /* @__PURE__ */ t(H, { name: "reason", label: e("Reason"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(fe, { submitLabel: e("Send to HR"), onCancel: () => a(l.me), dirtyHint: !1 })
    ] })
  ] });
}
function wa() {
  const a = N(), r = ne(), n = O(), o = ie(Z().name), { data: s, isLoading: c, error: i, mutate: d } = A(v.payoutRequestRecord, { name: o }), y = ot(i, d), p = W(v.sendPayoutChange), f = W(v.withdrawPayoutChange), [u, h] = q(!1), g = async () => {
    try {
      await at(() => p.run({ name: o }), r.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it.")), await d();
    } catch {
    }
  }, x = s?.mine && s.status === "Draft" ? /* @__PURE__ */ t(w, { loading: p.loading, onClick: g, children: e("Send to HR") }) : s?.mine && s.status === "Waiting for HR" ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => h(!0), children: e("Withdraw") }) : void 0;
  return /* @__PURE__ */ m(
    Q,
    {
      title: s?.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
      subtitle: o,
      meta: s && /* @__PURE__ */ t($, { value: s.status }),
      onBack: () => a(l.me),
      actions: x,
      loading: c,
      error: y.error,
      onRetry: d,
      children: [
        y.needed && /* @__PURE__ */ t(We, { what: e("This request shows once you confirm it is you."), busy: y.busy, onConfirm: y.confirm }),
        s && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
          p.errorMessage && /* @__PURE__ */ t(S, { tone: "error", children: p.errorMessage }),
          s.status === "Waiting for HR" && /* @__PURE__ */ t(S, { tone: "info", children: e("HR confirms it on the desk. You are told either way.") }),
          /* @__PURE__ */ t(
            U,
            {
              items: [
                { label: e("Bank"), value: s.bank, hideWhenEmpty: !0 },
                { label: e("Account No."), value: s.account_no, hideWhenEmpty: !0 },
                { label: e("Account Name"), value: s.account_name, hideWhenEmpty: !0 },
                { label: e("Mobile No."), value: s.mobile_no, hideWhenEmpty: !0 },
                { label: e("Provider"), value: s.provider, hideWhenEmpty: !0 },
                { label: e("Evidence"), value: s.change === "Bank Account" ? s.has_evidence ? e("Attached") : e("Missing") : null, hideWhenEmpty: !0 },
                { label: e("Sent On"), value: s.sent_on ? Ce(s.sent_on) : null, hideWhenEmpty: !0 },
                { label: e("Effective From"), value: s.effective_from ? _(s.effective_from) : null, hideWhenEmpty: !0 },
                { label: e("Decision Note"), value: s.decision_note, hideWhenEmpty: !0, full: !0 },
                { label: e("Reason"), value: s.reason, hideWhenEmpty: !0, full: !0 }
              ]
            }
          )
        ] }),
        /* @__PURE__ */ t(
          bt,
          {
            open: u,
            onClose: () => h(!1),
            title: e("Withdraw this request?"),
            confirmLabel: e("Withdraw"),
            destructive: !0,
            onConfirm: async () => {
              await f.run({ name: o }), n.success(e("Request withdrawn.")), await d();
            },
            children: e("HR will not act on it. Your pay keeps going where it goes now.")
          }
        )
      ]
    }
  );
}
function ba() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.expenseList);
  return /* @__PURE__ */ t(
    oe,
    {
      title: e("Expense Claims"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.expenseNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("New Expense Claim")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Ge, {}), title: e("No expense claims yet"), description: e("Claim what you spent for work, with a photo of each receipt.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        M,
        {
          primary: F(i.total_claimed_amount, i.currency),
          secondary: _(i.posting_date || i.creation),
          action: /* @__PURE__ */ t($, { value: i.docstatus === 0 ? i.approval_status || "Draft" : i.status }),
          onClick: () => a(l.expenseRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function Ca() {
  const a = N(), r = O(), n = A(v.expenseOptions), o = W(v.claimExpenses), s = me(
    () => ee.object({
      lines: ee.array(ee.object({ expense_type: le(() => e("Expense Type")), amount: kt(() => e("Amount"), { min: 0.01 }) }).loose()).min(1)
    }).loose(),
    []
  ), c = () => ({ lines: [{ expense_date: J(), expense_type: "", amount: null, description: "" }], remark: "", receipts: [] }), i = pe({ schema: s, defaultValues: c() }), d = Me(ne().user, "expense-claim", "new"), [y, p] = q(null);
  ue(() => {
    d.restored && Array.isArray(d.restored.value?.lines) && d.restored.value.lines.length && (i.reset({ ...c(), ...d.restored.value, receipts: [] }), p(d.restored.saved), d.dismiss());
    const h = i.watch((g) => d.keep({ lines: g.lines ?? [], remark: g.remark ?? "" }));
    return () => h.unsubscribe();
  }, []);
  const f = () => {
    d.clear(), p(null), i.reset(c());
  }, u = async (h) => {
    const g = await o.run({ lines: JSON.stringify(h.lines), remark: h.remark });
    d.clear();
    const x = [];
    for (const E of h.receipts ?? [])
      try {
        await vt(E, { doctype: "Expense Claim", docname: g, isPrivate: !0 });
      } catch {
        x.push(E.name);
      }
    x.length ? r.warning(e("The claim was saved, but {0} receipts did not upload. Add them on a computer.", [String(x.length)])) : r.success(e("Claim sent to {0}.", [n.data?.approver_name ?? e("your expense approver")])), a(l.expenseRecord(g));
  };
  return /* @__PURE__ */ m(ae, { title: e("New Expense Claim"), onBack: () => a(l.expenses), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    y !== null && /* @__PURE__ */ t(S, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: f, children: e("Start Again") }), children: e("You started this claim on {0}. Add the receipts again before you send it.", [_(qe(y))]) }),
    n.data && /* @__PURE__ */ t(S, { tone: n.data.approver_name ? "info" : "warning", children: _e(n.data.approver_name) }),
    /* @__PURE__ */ m(ye, { form: i, onSubmit: u, children: [
      /* @__PURE__ */ t(
        De,
        {
          name: "lines",
          label: e("Expenses"),
          minRows: 1,
          addLabel: e("Add an Expense"),
          newRow: () => ({ expense_date: J(), expense_type: "", amount: null, description: "" }),
          renderRow: (h) => /* @__PURE__ */ m(de, { children: [
            /* @__PURE__ */ t(se, { name: h("expense_type"), label: e("Expense Type"), required: !0, options: (n.data?.types ?? []).map((g) => ({ value: g.name, label: g.name, description: g.description ?? void 0 })) }),
            /* @__PURE__ */ t(Te, { name: h("amount"), label: e("Amount ({0})", [n.data?.currency ?? ""]), required: !0, min: 0, step: 0.01 }),
            /* @__PURE__ */ t(he, { name: h("expense_date"), label: e("Date"), maxDate: J() }),
            /* @__PURE__ */ t(H, { name: h("description"), label: e("Description") })
          ] })
        }
      ),
      /* @__PURE__ */ t(_t, { name: "receipts", label: e("Receipts"), multiple: !0, upload: !1, accept: "image/*,application/pdf", hint: e("Take a photo of each receipt, or choose a file. Only you, your approver and HR can open them.") }),
      /* @__PURE__ */ t(H, { name: "remark", label: e("Note"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(fe, { submitLabel: e("Send Claim"), onCancel: () => a(l.expenses) })
    ] })
  ] });
}
function Ra() {
  const a = N(), r = ie(Z().name), { data: n, isLoading: o, error: s, mutate: c } = A(v.expenseRecord, { name: r });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n ? F(n.total_claimed_amount, n.currency) : e("Expense Claim"),
      subtitle: n && (n.mine ? r : n.employee_name),
      meta: n && /* @__PURE__ */ t($, { value: n.docstatus === 0 ? n.approval_status || "Draft" : n.status }),
      onBack: () => a(l.expenses),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        /* @__PURE__ */ t(
          U,
          {
            items: [
              { label: e("Claimed"), value: F(n.total_claimed_amount, n.currency) },
              { label: e("Approved Amount"), value: n.docstatus === 1 ? F(n.total_sanctioned_amount, n.currency) : null, hideWhenEmpty: !0 },
              { label: e("Expense Approver"), value: n.approver_name, hideWhenEmpty: !0 },
              { label: e("Note"), value: n.remark, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(B, { title: e("Expenses"), children: /* @__PURE__ */ t(T, { divided: !0, children: n.expenses.map((i, d) => /* @__PURE__ */ t(M, { primary: `${i.expense_type} · ${F(i.amount, n.currency)}`, secondary: [_(i.expense_date), i.description ?? ""].filter(Boolean).join(" · ") }, d)) }) }),
        n.receipts.length > 0 && /* @__PURE__ */ t(B, { title: e("Receipts"), children: /* @__PURE__ */ t(T, { divided: !0, children: n.receipts.map((i) => /* @__PURE__ */ t(M, { primary: i.file_name, href: i.file_url }, i.name)) }) })
      ] })
    }
  );
}
function xa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.advanceList);
  return /* @__PURE__ */ t(
    oe,
    {
      title: e("Advances"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.advanceNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("Request an Advance")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t($t, {}), title: e("No advances"), description: e("Money paid to you ahead of work shows here, with what is left to settle.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        M,
        {
          primary: i.purpose,
          secondary: i.to_settle > 0 ? e("{0} · {1} left to settle", [F(i.advance_amount, i.currency), F(i.to_settle, i.currency)]) : F(i.advance_amount, i.currency),
          action: /* @__PURE__ */ t($, { value: i.docstatus === 0 ? "Draft" : i.status }),
          onClick: () => a(l.advanceRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function Aa() {
  const a = N(), r = O(), n = W(v.requestAdvance), o = me(() => ee.object({ purpose: le(() => e("Purpose")), amount: kt(() => e("Amount"), { min: 1 }) }), []), s = pe({ schema: o, defaultValues: { purpose: "", amount: null } });
  return /* @__PURE__ */ t(ae, { title: e("Request an Advance"), onBack: () => a(l.advances), children: /* @__PURE__ */ m(
    ye,
    {
      form: s,
      onSubmit: async (c) => {
        const i = await n.run({ purpose: c.purpose, amount: c.amount });
        r.success(e("Advance requested.")), a(l.advanceRecord(i));
      },
      children: [
        /* @__PURE__ */ t(H, { name: "purpose", label: e("Purpose"), required: !0, multiline: !0, rows: 2, hint: e("What the money is for, e.g. a field visit.") }),
        /* @__PURE__ */ t(Te, { name: "amount", label: e("Amount"), required: !0, min: 1, step: 1 }),
        /* @__PURE__ */ t(fe, { submitLabel: e("Request"), onCancel: () => a(l.advances) })
      ]
    }
  ) });
}
function Na() {
  const a = N(), r = ie(Z().name), { data: n, isLoading: o, error: s, mutate: c } = A(v.advanceRecord, { name: r });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n?.purpose ?? e("Advance"),
      subtitle: n && (n.mine ? r : n.employee_name),
      meta: n && /* @__PURE__ */ t($, { value: n.docstatus === 0 ? "Draft" : n.status }),
      onBack: () => a(l.advances),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ t(
        U,
        {
          items: [
            { label: e("Amount"), value: F(n.advance_amount, n.currency) },
            { label: e("Paid"), value: F(n.paid_amount, n.currency) },
            { label: e("Claimed"), value: F(n.claimed_amount, n.currency) },
            { label: e("Returned"), value: F(n.return_amount, n.currency) },
            { label: e("Left to Settle"), value: F(n.to_settle, n.currency) },
            { label: e("Requested On"), value: _(n.posting_date) }
          ]
        }
      )
    }
  );
}
function Sa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.payslips), i = ot(o, s);
  return /* @__PURE__ */ t(oe, { title: e("Payslips"), onBack: () => a(""), loading: n, error: i.error, onRetry: s, children: i.needed ? /* @__PURE__ */ t(We, { what: e("Your payslips show once you confirm it is you."), busy: i.busy, onConfirm: i.confirm }) : c && !r?.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Xt, {}), title: e("No payslips yet"), description: e("Your payslips show here once payroll is run.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r ?? []).map((d) => /* @__PURE__ */ t(
    M,
    {
      primary: e("{0} to {1}", [_(d.start_date), _(d.end_date)]),
      secondary: e("Net pay {0}", [F(d.net_pay, d.currency)]),
      onClick: () => a(l.payRecord(d.name))
    },
    d.name
  )) }) });
}
function Da() {
  const a = N(), r = ie(Z().name), { data: n, isLoading: o, error: s, mutate: c } = A(v.payslipRecord, { name: r }), i = ot(s, c), d = ne(), y = O(), p = W(v.confirmScreen), f = async () => {
    try {
      await at(() => p.run({ screen: "payslips" }), d.verify);
    } catch (g) {
      g instanceof nt || y.error(e("The payslip could not be opened. Try again."));
      return;
    }
    const u = On(r), h = window.open(u, "_blank");
    h ? h.opener = null : window.location.assign(u);
  };
  return /* @__PURE__ */ m(
    Q,
    {
      title: n ? e("{0} to {1}", [_(n.start_date), _(n.end_date)]) : e("Payslip"),
      subtitle: n?.employee_name,
      onBack: () => a(l.pay),
      actions: n ? /* @__PURE__ */ m(w, { loading: p.loading, onClick: f, children: [
        /* @__PURE__ */ t($n, {}),
        e("Open Payslip")
      ] }) : void 0,
      loading: o,
      error: i.error,
      onRetry: c,
      children: [
        i.needed && /* @__PURE__ */ t(We, { what: e("This payslip shows once you confirm it is you."), busy: i.busy, onConfirm: i.confirm }),
        n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
          /* @__PURE__ */ t(
            U,
            {
              items: [
                { label: e("Gross Pay"), value: F(n.gross_pay, n.currency) },
                { label: e("Total Deduction"), value: F(n.total_deduction, n.currency) },
                { label: e("Net Pay"), value: F(n.net_pay, n.currency) }
              ]
            }
          ),
          /* @__PURE__ */ t(B, { title: e("Earnings"), children: /* @__PURE__ */ t(T, { divided: !0, children: n.earnings.map((u) => /* @__PURE__ */ t(M, { primary: u.component, action: F(u.amount, n.currency) }, u.component)) }) }),
          /* @__PURE__ */ t(B, { title: e("Deductions"), children: /* @__PURE__ */ t(T, { divided: !0, children: n.deductions.map((u) => /* @__PURE__ */ t(M, { primary: u.component, action: F(u.amount, n.currency) }, u.component)) }) })
        ] })
      ]
    }
  );
}
function La() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.timesheets);
  return /* @__PURE__ */ m(
    oe,
    {
      title: e("Timesheets"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: r?.weekly ? /* @__PURE__ */ m(w, { onClick: () => a(l.week(et(J()))), children: [
        /* @__PURE__ */ t(Ue, {}),
        e("This Week")
      ] }) : void 0,
      children: [
        r && !r.weekly && /* @__PURE__ */ t(S, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer; they show here.") }),
        c && !r?.timesheets.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Ue, {}), title: e("No timesheets yet"), description: e("Your timesheets show here, newest first.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r?.timesheets ?? []).map((i) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} to {1}", [_(i.start_date), _(i.end_date)]),
            secondary: e("{0} hours", [String(i.total_hours ?? 0)]),
            action: /* @__PURE__ */ t($, { value: i.docstatus === 1 ? "Approved" : i.custom_approval_state || i.status }),
            onClick: () => a(r?.weekly && i.custom_week_start ? l.week(i.custom_week_start) : l.timesheetRecord(i.name))
          },
          i.name
        )) })
      ]
    }
  );
}
function ht(a) {
  return a === "Rest day" ? e("Rest Day") : a === "Public holiday" ? e("Public Holiday") : null;
}
function mt(a) {
  const r = ((/* @__PURE__ */ new Date(`${a}T12:00:00Z`)).getUTCDay() + 6) % 7;
  return [e("Monday"), e("Tuesday"), e("Wednesday"), e("Thursday"), e("Friday"), e("Saturday"), e("Sunday")][r];
}
function Ta() {
  const a = N(), r = O(), n = et(Z().week || J()), { data: o, isLoading: s, error: c, mutate: i } = A(v.timesheetWeek, { week_start: n }), d = W(v.saveTimesheetWeek), y = W(v.timesheetClaim), [p, f] = q([]), [u, h] = q(() => {
    const R = J();
    return R >= n && R <= ke(n, 6) ? Ke(n).indexOf(R) : 0;
  }), [g, x] = q(!1), E = be(!1), D = (R) => {
    E.current = R, x(R);
  }, L = Me(ne().user, "timesheet-week", n), [I, V] = q(null), z = (R) => R.timesheet?.entries.length ? R.timesheet.entries : [dt([], R.default_activity_type)], G = be(null);
  ue(() => {
    if (!o || o.week_start !== n) return;
    const R = G.current === n;
    if (G.current = n, R && E.current) return;
    const K = o.weekly && (!o.timesheet || o.timesheet.can_edit), Y = L.key ? Xe(L.key) : null;
    if (Y && K && Array.isArray(Y.value) && Y.value.length) {
      f(Y.value), D(!0), V(Y.saved);
      return;
    }
    Y && L.key && en(L.key), f(z(o)), D(!1), V(null);
  }, [o, n]);
  const j = Ke(n), b = o?.days[u], C = !!o?.weekly && (!o.timesheet || o.timesheet.can_edit), $e = me(() => (o?.activity_types ?? []).map((R) => ({ value: R, label: R })), [o]), ce = (R) => {
    f(R), D(!0), L.keep(R);
  }, an = () => {
    L.clear(), V(null), o && f(z(o)), D(!1);
  }, rt = async (R) => {
    try {
      const K = await d.run({ week_start: n, entries: JSON.stringify(Kn(p)), send: R ? 1 : 0 });
      return r.success(R ? e("Week sent for approval.") : e("Week saved.")), L.clear(), V(null), D(!1), await i(), K;
    } catch {
      return null;
    }
  }, on = o?.timesheet?.can_claim ? /* @__PURE__ */ t(
    w,
    {
      onClick: async () => {
        try {
          a(l.toilRecord(await y.run({ name: o.timesheet.name })));
        } catch {
        }
      },
      loading: y.loading,
      children: e("Claim as Time Off in Lieu")
    }
  ) : C ? /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(w, { variant: "outline", loading: d.loading, disabled: !g, onClick: () => rt(!1), children: e("Save") }),
    o?.approval && /* @__PURE__ */ t(w, { loading: d.loading, onClick: () => rt(!0), children: e("Send for Approval") })
  ] }) : void 0;
  return /* @__PURE__ */ t(
    ae,
    {
      title: e("Week of {0}", [_(n)]),
      subtitle: e("{0} hours this week", [String(Un(p))]),
      meta: o?.timesheet && /* @__PURE__ */ t($, { value: o.timesheet.docstatus === 1 ? "Approved" : o.timesheet.state }),
      onBack: () => a(l.timesheet),
      actions: on,
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        (d.errorMessage || y.errorMessage) && /* @__PURE__ */ t(S, { tone: "error", children: d.errorMessage || y.errorMessage }),
        I !== null && /* @__PURE__ */ t(
          S,
          {
            tone: "info",
            title: e("Restored From This Phone"),
            action: /* @__PURE__ */ t(w, { onClick: an, children: e("Discard") }),
            children: e("What you entered on {0} was not saved yet. Save or send it when you are ready.", [_(qe(I))])
          }
        ),
        !o.weekly && /* @__PURE__ */ t(S, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer.") }),
        C && o.approval && /* @__PURE__ */ t(S, { tone: o.approver_name ? "info" : "warning", children: _e(o.approver_name) }),
        o.timesheet?.state === "Returned" && o.timesheet.return_reason && /* @__PURE__ */ t(S, { tone: "warning", title: e("Returned to You"), children: o.timesheet.return_reason }),
        /* @__PURE__ */ m("div", { className: "flex items-center justify-between gap-2", children: [
          /* @__PURE__ */ t(Fe, { label: e("Previous Day"), variant: "outline", onClick: () => u > 0 ? h(u - 1) : a(l.week(ke(n, -7))), children: /* @__PURE__ */ t(qn, {}) }),
          /* @__PURE__ */ m("div", { className: "flex flex-col items-center", children: [
            /* @__PURE__ */ t(te, { size: "lg", children: mt(j[u]) }),
            /* @__PURE__ */ t(te, { size: "sm", muted: !0, children: _(j[u]) })
          ] }),
          /* @__PURE__ */ t(Fe, { label: e("Next Day"), variant: "outline", onClick: () => u < 6 ? h(u + 1) : a(l.week(ke(n, 7))), children: /* @__PURE__ */ t(St, {}) })
        ] }),
        /* @__PURE__ */ m("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ t(we, { children: e("{0} hours entered", [String(Qt(p, u))]) }),
          b?.attendance_hours !== null && b?.attendance_hours !== void 0 && /* @__PURE__ */ t(we, { variant: "outline", children: e("Attendance {0} hours", [String(b.attendance_hours)]) }),
          b && ht(b.kind) && /* @__PURE__ */ t(we, { tone: "info", children: ht(b.kind) }),
          b?.leave && /* @__PURE__ */ t(we, { tone: "warning", children: b.leave_fraction === 0.5 ? e("Half Day of Leave") : e("On Leave") })
        ] }),
        p.map((R) => /* @__PURE__ */ t(_n, { children: /* @__PURE__ */ m(kn, { className: "flex flex-col gap-3", children: [
          /* @__PURE__ */ m("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(Ne, { htmlFor: `activity-${R.row}`, children: e("Activity Type") }),
            /* @__PURE__ */ t(
              wn,
              {
                id: `activity-${R.row}`,
                value: R.activity_type,
                options: $e,
                disabled: !C,
                onValueChange: (K) => ce(p.map((Y) => Y.row === R.row ? { ...Y, activity_type: K } : Y))
              }
            )
          ] }),
          /* @__PURE__ */ m("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(Ne, { htmlFor: `description-${R.row}`, children: e("Description") }),
            /* @__PURE__ */ t(
              je,
              {
                id: `description-${R.row}`,
                value: R.description ?? "",
                disabled: !C,
                onChange: (K) => ce(p.map((Y) => Y.row === R.row ? { ...Y, description: K.target.value } : Y))
              }
            )
          ] }),
          /* @__PURE__ */ m("div", { className: "flex items-end gap-2", children: [
            /* @__PURE__ */ m("div", { className: "flex flex-1 flex-col gap-1", children: [
              /* @__PURE__ */ t(Ne, { htmlFor: `hours-${R.row}`, children: e("Hours on {0}", [mt(j[u])]) }),
              /* @__PURE__ */ t(
                je,
                {
                  id: `hours-${R.row}`,
                  type: "number",
                  inputMode: "decimal",
                  min: 0,
                  max: 24,
                  step: 0.25,
                  value: R.hours[u] ? String(R.hours[u]) : "",
                  disabled: !C,
                  onChange: (K) => ce(Gn(p, R.row, u, K.target.value))
                }
              )
            ] }),
            C && p.length > 1 && /* @__PURE__ */ t(Fe, { label: e("Remove Line"), variant: "ghost", onClick: () => ce(p.filter((K) => K.row !== R.row)), children: /* @__PURE__ */ t(Hn, {}) })
          ] })
        ] }) }, R.row)),
        C && /* @__PURE__ */ m("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ m(w, { variant: "outline", onClick: () => ce([...p, dt(p, o.default_activity_type)]), children: [
            /* @__PURE__ */ t(ve, {}),
            e("Add Line")
          ] }),
          o.previous_entries.length > 0 && /* @__PURE__ */ m(w, { variant: "outline", onClick: () => ce(Jn(o.previous_entries)), children: [
            /* @__PURE__ */ t(Wn, {}),
            e("Copy Last Week")
          ] })
        ] }),
        o.checks.length > 0 && /* @__PURE__ */ t(B, { title: e("Weekly Check"), children: /* @__PURE__ */ t(T, { divided: !0, children: o.checks.map((R) => /* @__PURE__ */ t(M, { primary: R }, R)) }) })
      ] })
    }
  );
}
function Ma() {
  const a = N(), r = ie(Z().name), { data: n, isLoading: o, error: s, mutate: c } = A(v.timesheetRecord, { name: r });
  return /* @__PURE__ */ t(
    Q,
    {
      title: e("Timesheet"),
      subtitle: n && (n.mine ? r : n.employee_name),
      meta: n && /* @__PURE__ */ t($, { value: n.docstatus === 1 ? "Approved" : n.state }),
      onBack: () => a(l.timesheet),
      actions: n?.mine && n.week_start ? /* @__PURE__ */ t(w, { onClick: () => a(l.week(n.week_start)), children: e("Open the Week") }) : void 0,
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          U,
          {
            items: [
              { label: e("From"), value: _(n.start_date) },
              { label: e("To"), value: _(n.end_date) },
              { label: e("Total Hours"), value: String(n.total_hours ?? 0) }
            ]
          }
        ),
        /* @__PURE__ */ t(T, { divided: !0, children: n.lines.map((i, d) => /* @__PURE__ */ t(M, { primary: e("{0} · {1} hours", [_(i.date), String(i.hours)]), secondary: [i.activity_type, i.description].filter(Boolean).join(" · ") }, d)) })
      ] })
    }
  );
}
function qa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.toilList);
  return /* @__PURE__ */ m(
    oe,
    {
      title: e("Time Off in Lieu"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: r?.eligible ? /* @__PURE__ */ m(w, { onClick: () => a(l.toilNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("Claim Time Off")
      ] }) : void 0,
      children: [
        r && !r.eligible && /* @__PURE__ */ t(S, { tone: "info", children: e("Your grade does not bank extra hours as time off. Ask HR if you think it should.") }),
        r?.eligible && /* @__PURE__ */ m(Ct, { columns: 2, children: [
          /* @__PURE__ */ t(ze, { label: e("Days Left"), value: String(r.left) }),
          /* @__PURE__ */ t(
            ze,
            {
              label: e("Lapsing in 30 Days"),
              value: String(r.lapsing),
              hint: r.first_lapse ? e("First on {0}", [_(r.first_lapse)]) : void 0
            }
          )
        ] }),
        c && !r?.claims.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(Je, {}), title: e("No claims yet"), description: e("Claim the extra hours you worked, a day at a time.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r?.claims ?? []).map((i) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} hours · {1} days", [String(i.total_hours ?? 0), String(i.days ?? 0)]),
            secondary: i.status === "Approved" && i.lapses_on ? e("{0} days left, usable until {1}", [String(i.days_left ?? 0), _(i.lapses_on)]) : _(i.creation),
            action: /* @__PURE__ */ t($, { value: i.status }),
            onClick: () => a(l.toilRecord(i.name))
          },
          i.name
        )) })
      ]
    }
  );
}
const pt = () => ({ work_date: "", hours: null, work_done: "" });
function Wa() {
  const a = N(), r = O(), [n] = ft(), o = n.get("claim"), s = A(v.toilList), c = A(v.toilRecord, { name: o ?? "" }, { enabled: !!o }), i = W(v.saveToilClaim), d = un(), [y, p] = q(!1), [f, u] = q(null), h = pe({ defaultValues: { lines: [pt()], note: "" } });
  ue(() => {
    c.data && h.reset({ lines: c.data.lines.map((D) => ({ work_date: D.work_date, hours: D.hours, work_done: D.work_done })), note: c.data.note ?? "" });
  }, [c.data, h]);
  const g = async () => {
    if (s.data) {
      p(!0), u(null);
      try {
        const D = s.data.from_attendance ? "Attendance" : "Timesheet", L = J(), I = await d.get(v.extraTime, { employee: s.data.employee, from_date: ke(L, -30), to_date: L, source: D }) ?? [], V = h.getValues("lines").filter((z) => z.work_date);
        h.setValue("lines", ha(V, I), { shouldDirty: !0 }), u(I.length ? e("{0} days found in the last 30 days. Say what the work was on each.", [String(I.length)]) : e("The records show no extra hours you have not claimed in the last 30 days."));
      } catch {
        u(e("The records could not be read. Enter the days yourself."));
      } finally {
        p(!1);
      }
    }
  }, x = async (D) => {
    const L = await i.run({ lines: JSON.stringify(D.lines.filter((I) => I.work_date)), note: D.note, name: o ?? void 0 });
    r.success(e("Claim saved. Send it when it is ready.")), a(l.toilRecord(L));
  }, E = s.data && (s.data.from_attendance || s.data.from_timesheets);
  return /* @__PURE__ */ m(
    ae,
    {
      title: o ? e("Change Claim") : e("Claim Time Off"),
      onBack: () => a(o ? l.toilRecord(o) : l.toil),
      loading: s.isLoading || c.isLoading,
      error: s.error ?? c.error,
      actions: E ? /* @__PURE__ */ t(w, { variant: "outline", loading: y, onClick: g, children: e("Fill from Records") }) : void 0,
      children: [
        s.data && /* @__PURE__ */ t(S, { tone: s.data.approver_name ? "info" : "warning", children: _e(s.data.approver_name) }),
        f && /* @__PURE__ */ t(S, { tone: "info", children: f }),
        /* @__PURE__ */ m(ye, { form: h, onSubmit: x, children: [
          /* @__PURE__ */ t(
            De,
            {
              name: "lines",
              label: e("Days Worked"),
              minRows: 1,
              addLabel: e("Add a Day"),
              newRow: pt,
              renderRow: (D) => /* @__PURE__ */ m(de, { children: [
                /* @__PURE__ */ t(he, { name: D("work_date"), label: e("Date"), required: !0, maxDate: J() }),
                /* @__PURE__ */ t(Te, { name: D("hours"), label: e("Hours Worked"), min: 0, max: 24, step: 0.25 }),
                /* @__PURE__ */ t(H, { name: D("work_done"), label: e("Work Done"), required: !0, multiline: !0, rows: 2 })
              ] })
            }
          ),
          /* @__PURE__ */ t(H, { name: "note", label: e("Note"), multiline: !0, rows: 2, hint: e("Anything your approver should know about these days.") }),
          /* @__PURE__ */ t(fe, { submitLabel: e("Save Claim"), onCancel: () => a(o ? l.toilRecord(o) : l.toil) })
        ] })
      ]
    }
  );
}
function $a() {
  const a = N(), r = O(), n = ie(Z().name), { data: o, isLoading: s, error: c, mutate: i } = A(v.toilRecord, { name: n }), d = W(v.toilAction), y = async (f) => {
    try {
      await d.run({ name: n, action: f }), r.success(e("Claim sent.")), await i();
    } catch {
    }
  }, p = o && /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    o.can_edit && /* @__PURE__ */ t(w, { variant: "outline", onClick: () => a(`${l.toilNew}?claim=${encodeURIComponent(n)}`), children: e("Change") }),
    o.actions.map((f) => /* @__PURE__ */ t(w, { loading: d.loading, onClick: () => y(f), children: f === "Send for Authorisation" ? e("Send for Authorisation") : e("Send for Approval") }, f)),
    o.mine && o.status === "Approved" && (o.days_left ?? 0) > 0 && o.leave_type && /* @__PURE__ */ t(w, { onClick: () => a(`${l.leaveNew}?type=${encodeURIComponent(o.leave_type ?? "")}`), children: e("Apply for Leave") })
  ] });
  return /* @__PURE__ */ t(
    Q,
    {
      title: e("Time Off in Lieu Claim"),
      subtitle: o && !o.mine ? o.employee_name : n,
      meta: o && /* @__PURE__ */ t($, { value: o.status }),
      onBack: () => a(l.toil),
      actions: p,
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        d.errorMessage && /* @__PURE__ */ t(S, { tone: "error", children: d.errorMessage }),
        o.stage.items.length > 0 && /* @__PURE__ */ t(S, { tone: o.stage.tone, children: /* @__PURE__ */ t("div", { className: "flex flex-col gap-1", children: o.stage.items.map((f) => /* @__PURE__ */ m(te, { children: [
          /* @__PURE__ */ m("strong", { children: [
            f.label,
            ":"
          ] }),
          " ",
          f.text
        ] }, f.label)) }) }),
        /* @__PURE__ */ t(
          U,
          {
            items: [
              { label: e("Total Extra Hours"), value: String(o.total_hours ?? 0) },
              { label: e("Time Off (Days)"), value: String(o.days ?? 0) },
              { label: e("Approver"), value: o.approver_name, hideWhenEmpty: !0 },
              { label: e("Days Left"), value: o.days_left === null ? null : String(o.days_left), hideWhenEmpty: !0 },
              { label: e("Usable Until"), value: o.lapses_on ? _(o.lapses_on) : null, hideWhenEmpty: !0 },
              { label: e("Note"), value: o.note, hideWhenEmpty: !0, full: !0 },
              { label: e("Approver's Note"), value: o.decision_note, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(B, { title: e("Days Worked"), children: /* @__PURE__ */ t(T, { divided: !0, children: o.lines.map((f) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} · {1} hours", [_(f.work_date), String(f.hours ?? f.planned_hours ?? 0)]),
            secondary: [f.work_done, f.supported_by ?? ""].filter(Boolean).join(" · ")
          },
          f.work_date
        )) }) })
      ] })
    }
  );
}
function tn(a) {
  return a.travel_from && a.travel_to ? e("{0} to {1}", [a.travel_from, a.travel_to]) : a.travel_to || a.travel_from || a.purpose_of_travel;
}
function Ea() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = A(v.travelList);
  return /* @__PURE__ */ t(
    oe,
    {
      title: e("Travel Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.travelNew), children: [
        /* @__PURE__ */ t(ve, {}),
        e("New Travel Request")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(re, { icon: /* @__PURE__ */ t(It, {}), title: e("No travel requests yet"), description: e("Ask to travel for work. Your line manager approves it.") }) : /* @__PURE__ */ t(T, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        M,
        {
          primary: tn(i),
          secondary: [i.purpose_of_travel, i.departure_date ? _(i.departure_date) : _(i.creation)].filter(Boolean).join(" · "),
          action: /* @__PURE__ */ t($, { value: i.state }),
          onClick: () => a(l.travelRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
const nn = () => ({ travel_from: "", travel_to: "", mode_of_travel: "", departure_date: "", arrival_date: "", lodging_required: !1 }), Pa = () => ({ expense_type: "", total_amount: null, comments: "" }), Oe = () => ({ travel_type: "", purpose_of_travel: "", travel_funding: "", description: "", itinerary: [nn()], costings: [] });
function Se(a) {
  switch (a) {
    case "Domestic":
      return e("Domestic");
    case "International":
      return e("International");
    case "Require Full Funding":
      return e("Require Full Funding");
    case "Fully Sponsored":
      return e("Fully Sponsored");
    case "Partially Sponsored, Require Partial Funding":
      return e("Partially Sponsored, Require Partial Funding");
    case "Flight":
      return e("Flight");
    case "Train":
      return e("Train");
    case "Taxi":
      return e("Taxi");
    case "Rented Car":
      return e("Rented Car");
    default:
      return a;
  }
}
function Fa() {
  const a = N(), r = O(), n = A(v.travelOptions), o = W(v.requestTravel), s = me(
    () => ee.object({
      travel_type: le(() => e("Travel Type")),
      purpose_of_travel: le(() => e("Purpose of Travel")),
      itinerary: ee.array(ee.object({ travel_from: le(() => e("From")), travel_to: le(() => e("To")) }).loose()).min(1)
    }).loose(),
    []
  ), c = pe({ schema: s, defaultValues: Oe() }), i = Me(ne().user, "travel-request", "new"), [d, y] = q(null);
  ue(() => {
    i.restored && Array.isArray(i.restored.value?.itinerary) && (c.reset({ ...Oe(), ...i.restored.value }), y(i.restored.saved), i.dismiss());
    const h = c.watch((g) => i.keep(g));
    return () => h.unsubscribe();
  }, []);
  const p = () => {
    i.clear(), y(null), c.reset(Oe());
  }, f = async (h) => {
    const g = pa(h.itinerary, h.costings), x = await o.run({
      travel_type: h.travel_type,
      purpose_of_travel: h.purpose_of_travel,
      travel_funding: h.travel_funding || void 0,
      description: h.description,
      itinerary: JSON.stringify(g.itinerary),
      costings: JSON.stringify(g.costings),
      send: 1
    });
    i.clear(), r.success(n.data?.approver_name ? e("Travel request sent to {0}.", [n.data.approver_name]) : e("Travel request sent.")), a(l.travelRecord(x.name));
  }, u = (h) => (h ?? []).map((g) => ({ value: g, label: Se(g) }));
  return /* @__PURE__ */ m(ae, { title: e("New Travel Request"), onBack: () => a(l.travel), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    d !== null && /* @__PURE__ */ t(S, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: p, children: e("Start Again") }), children: e("You started this request on {0} and had not sent it.", [_(qe(d))]) }),
    n.data && /* @__PURE__ */ t(S, { tone: n.data.approver_name ? "info" : "warning", children: _e(n.data.approver_name) }),
    /* @__PURE__ */ m(ye, { form: c, onSubmit: f, children: [
      /* @__PURE__ */ t(se, { name: "travel_type", label: e("Travel Type"), required: !0, options: u(n.data?.travel_types) }),
      /* @__PURE__ */ t(se, { name: "purpose_of_travel", label: e("Purpose of Travel"), required: !0, options: (n.data?.purposes ?? []).map((h) => ({ value: h, label: h })), hint: n.data && !n.data.purposes.length ? e("HR has not set up purposes of travel yet. Ask them to.") : void 0 }),
      /* @__PURE__ */ t(se, { name: "travel_funding", label: e("Travel Funding"), options: u(n.data?.funding) }),
      /* @__PURE__ */ t(
        De,
        {
          name: "itinerary",
          label: e("Journeys"),
          minRows: 1,
          addLabel: e("Add a Journey"),
          newRow: nn,
          renderRow: (h) => /* @__PURE__ */ m(de, { children: [
            /* @__PURE__ */ t(H, { name: h("travel_from"), label: e("From"), required: !0 }),
            /* @__PURE__ */ t(H, { name: h("travel_to"), label: e("To"), required: !0 }),
            /* @__PURE__ */ t(se, { name: h("mode_of_travel"), label: e("Mode of Travel"), options: u(n.data?.modes) }),
            /* @__PURE__ */ t(lt, { name: h("departure_date"), label: e("Departure") }),
            /* @__PURE__ */ t(lt, { name: h("arrival_date"), label: e("Arrival") }),
            /* @__PURE__ */ t(Ze, { name: h("lodging_required"), label: e("Lodging Required") })
          ] })
        }
      ),
      /* @__PURE__ */ t(
        De,
        {
          name: "costings",
          label: e("Expected Costs"),
          addLabel: e("Add a Cost"),
          newRow: Pa,
          emptyText: e("None yet. Add what the trip is expected to cost, if you know."),
          renderRow: (h) => /* @__PURE__ */ m(de, { children: [
            /* @__PURE__ */ t(se, { name: h("expense_type"), label: e("Expense Type"), options: (n.data?.expense_types ?? []).map((g) => ({ value: g, label: g })) }),
            /* @__PURE__ */ t(Te, { name: h("total_amount"), label: e("Amount ({0})", [n.data?.currency ?? ""]), min: 0, step: 0.01 }),
            /* @__PURE__ */ t(H, { name: h("comments"), label: e("Comments") })
          ] })
        }
      ),
      /* @__PURE__ */ t(H, { name: "description", label: e("Other Details"), multiline: !0, rows: 3 }),
      /* @__PURE__ */ t(fe, { submitLabel: e("Send for Approval"), onCancel: () => a(l.travel) })
    ] })
  ] });
}
function Ba() {
  const a = N(), r = O(), n = ie(Z().name), { data: o, isLoading: s, error: c, mutate: i } = A(v.travelRecord, { name: n }), d = W(v.travelAction), y = async () => {
    try {
      await d.run({ name: n, action: "Send for Approval" }), r.success(e("Travel request sent.")), await i();
    } catch {
    }
  };
  return /* @__PURE__ */ t(
    Q,
    {
      title: o ? tn({ ...o.itinerary[0] ?? { travel_from: null, travel_to: null }, purpose_of_travel: o.purpose_of_travel }) : e("Travel Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t($, { value: o.state }),
      onBack: () => a(l.travel),
      actions: o?.can_send ? /* @__PURE__ */ t(w, { loading: d.loading, onClick: y, children: e("Send for Approval") }) : void 0,
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        d.errorMessage && /* @__PURE__ */ t(S, { tone: "error", children: d.errorMessage }),
        o.mine && o.state === "Pending Approval" && /* @__PURE__ */ t(S, { tone: "info", children: _e(o.approver_name) }),
        /* @__PURE__ */ t(
          U,
          {
            items: [
              { label: e("Purpose of Travel"), value: o.purpose_of_travel },
              { label: e("Travel Type"), value: Se(o.travel_type) },
              { label: e("Travel Funding"), value: o.travel_funding ? Se(o.travel_funding) : null, hideWhenEmpty: !0 },
              { label: e("Line Manager"), value: o.approver_name, hideWhenEmpty: !0 },
              { label: e("Other Details"), value: o.description, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(B, { title: e("Journeys"), children: /* @__PURE__ */ t(T, { divided: !0, children: o.itinerary.map((p, f) => /* @__PURE__ */ t(
          M,
          {
            primary: e("{0} to {1}", [p.travel_from || "?", p.travel_to || "?"]),
            secondary: [p.mode_of_travel ? Se(p.mode_of_travel) : "", p.departure_date ? Ce(p.departure_date) : "", p.lodging_required ? e("Lodging required") : ""].filter(Boolean).join(" · ")
          },
          f
        )) }) }),
        o.costings.length > 0 && /* @__PURE__ */ t(B, { title: e("Expected Costs"), children: /* @__PURE__ */ t(T, { divided: !0, children: o.costings.map((p, f) => /* @__PURE__ */ t(M, { primary: p.expense_type || e("Other"), secondary: p.comments ?? void 0, action: o.currency ? F(p.total_amount, o.currency) : String(p.total_amount) }, f)) }) }),
        !o.mine && /* @__PURE__ */ t(te, { muted: !0, children: e("Decide this request from Approvals.") })
      ] })
    }
  );
}
const Ha = [
  { path: "leave", element: /* @__PURE__ */ t(ya, {}) },
  { path: "leave/new", element: /* @__PURE__ */ t(fa, {}) },
  { path: "leave/:name", element: /* @__PURE__ */ t(va, {}) },
  { path: "cover", element: /* @__PURE__ */ t(aa, {}) },
  { path: "cover/:name", element: /* @__PURE__ */ t(oa, {}) },
  { path: "toil", element: /* @__PURE__ */ t(qa, {}) },
  { path: "toil/new", element: /* @__PURE__ */ t(Wa, {}) },
  { path: "toil/:name", element: /* @__PURE__ */ t($a, {}) },
  { path: "timesheet", element: /* @__PURE__ */ t(La, {}) },
  { path: "timesheet/week/:week", element: /* @__PURE__ */ t(Ta, {}) },
  { path: "timesheet/:name", element: /* @__PURE__ */ t(Ma, {}) },
  { path: "expenses", element: /* @__PURE__ */ t(ba, {}) },
  { path: "expenses/new", element: /* @__PURE__ */ t(Ca, {}) },
  { path: "expenses/:name", element: /* @__PURE__ */ t(Ra, {}) },
  { path: "advances", element: /* @__PURE__ */ t(xa, {}) },
  { path: "advances/new", element: /* @__PURE__ */ t(Aa, {}) },
  { path: "advances/:name", element: /* @__PURE__ */ t(Na, {}) },
  { path: "pay", element: /* @__PURE__ */ t(Sa, {}) },
  { path: "pay/:name", element: /* @__PURE__ */ t(Da, {}) },
  { path: "check-in", element: /* @__PURE__ */ t(Zn, {}) },
  { path: "attendance", element: /* @__PURE__ */ t(Qn, {}) },
  { path: "attendance/new", element: /* @__PURE__ */ t(ea, {}) },
  { path: "attendance/:name", element: /* @__PURE__ */ t(ut, { doctype: "Attendance Request" }) },
  { path: "shifts", element: /* @__PURE__ */ t(ta, {}) },
  { path: "shifts/new", element: /* @__PURE__ */ t(na, {}) },
  { path: "shifts/:name", element: /* @__PURE__ */ t(ut, { doctype: "Shift Request" }) },
  { path: "me", element: /* @__PURE__ */ t(ga, {}) },
  { path: "me/payout/new", element: /* @__PURE__ */ t(ka, {}) },
  { path: "me/payout/:name", element: /* @__PURE__ */ t(wa, {}) },
  { path: "travel", element: /* @__PURE__ */ t(Ea, {}) },
  { path: "travel/new", element: /* @__PURE__ */ t(Fa, {}) },
  { path: "travel/:name", element: /* @__PURE__ */ t(Ba, {}) }
], Ga = ln({
  key: "seal_hrms.my_hr",
  home: ra,
  routes: Ha,
  records: Rt,
  settings: [{ key: "hr_notifications", label: "HR", kind: "push-category" }]
});
export {
  Ha as ROUTES,
  Ga as default
};
