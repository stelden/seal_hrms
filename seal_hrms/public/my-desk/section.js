var ln = Object.defineProperty;
var cn = (a, r, n) => r in a ? ln(a, r, { enumerable: !0, configurable: !0, writable: !0, value: n }) : a[r] = n;
var st = (a, r, n) => cn(a, typeof r != "symbol" ? r + "" : r, n);
import { jsx as t, jsxs as m, Fragment as de } from "react/jsx-runtime";
import { useShell as ce, defineSection as dn } from "@stelden/seal-frontend/section";
import { useContext as un, createContext as hn, forwardRef as ft, createElement as je, useCallback as xe, useState as T, useMemo as ue, useRef as Ce, useEffect as _e } from "react";
import { useParams as X, useSearchParams as vt } from "react-router";
import { useGet as x, usePost as M, formatDateTime as Re, formatDate as g, uploadFile as _t, formatCurrency as P, useFrappeCall as mn } from "@stelden/seal-frontend";
import { z as ae, required as ne, frappeDate as ke, useSealForm as he, SealForm as me, RadioInput as gt, DateInput as oe, CheckboxInput as qe, TextInput as H, FormActions as pe, SelectInput as le, FormSection as lt, AutocompleteInput as Pe, FileInput as kt, MobileInputKE as pn, amount as wt, RowsInput as Le, NumberInput as Me, DateTimeInput as ct } from "@stelden/seal-frontend/forms";
import { __ as e, toneMap as yn, StatusChip as fn, useNotify as B, FormPage as re, Alert as D, Button as w, Text as K, Section as O, List as W, ListItem as q, ListPage as ie, EmptyState as Z, DetailPage as Q, DescriptionList as V, ConfirmDialog as Qe, TabsNav as vn, TabPanel as Be, SealDialog as bt, Textarea as _n, DashboardPage as gn, StatGrid as Ct, StatCard as Ye, Badge as be, FilterChips as kn, Label as Ne, Input as Ve, IconButton as He, Card as wn, CardContent as bn, Select as Cn } from "@stelden/seal-frontend/ui";
const G = (a) => encodeURIComponent(a);
function se(a) {
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
  leaveRecord: (a) => `leave/${G(a)}`,
  cover: "cover",
  handover: (a) => `cover/${G(a)}`,
  toil: "toil",
  toilNew: "toil/new",
  toilRecord: (a) => `toil/${G(a)}`,
  timesheet: "timesheet",
  week: (a) => `timesheet/week/${a}`,
  timesheetRecord: (a) => `timesheet/${G(a)}`,
  expenses: "expenses",
  expenseNew: "expenses/new",
  expenseRecord: (a) => `expenses/${G(a)}`,
  advances: "advances",
  advanceNew: "advances/new",
  advanceRecord: (a) => `advances/${G(a)}`,
  pay: "pay",
  payRecord: (a) => `pay/${G(a)}`,
  checkIn: "check-in",
  attendance: "attendance",
  attendanceNew: "attendance/new",
  attendanceRecord: (a) => `attendance/${G(a)}`,
  shifts: "shifts",
  shiftNew: "shifts/new",
  shiftRecord: (a) => `shifts/${G(a)}`,
  me: "me",
  payoutNew: "me/payout/new",
  payoutRecord: (a) => `me/payout/${G(a)}`,
  travel: "travel",
  travelNew: "travel/new",
  travelRecord: (a) => `travel/${G(a)}`,
  compensatory: "compensatory-leave",
  compensatoryNew: "compensatory-leave/new",
  compensatoryRecord: (a) => `compensatory-leave/${G(a)}`
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
  "Travel Request": { list: l.travel, record: l.travelRecord, create: l.travelNew },
  "Compensatory Leave Request": { list: l.compensatory, record: l.compensatoryRecord, create: l.compensatoryNew }
};
function Rn(a) {
  return Rt[a]?.list;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const An = (a) => a?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function xn(a, r, n = []) {
  if (r == null)
    throw new Error("[lucide]: iconNode is required when icon name is used");
  return {
    name: An(a),
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
const Nn = (a) => {
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
const Dn = (a) => {
  const r = Nn(a);
  return r.charAt(0).toUpperCase() + r.slice(1);
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ue = (...a) => a.filter((r, n, o) => !!r && r.trim() !== "" && o.indexOf(r) === n).join(" ").trim();
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
function Oe(a) {
  return a != null;
}
function Ln(a, r = {}) {
  const n = r.attributeNames ?? {}, o = (d) => n[d] ?? d, s = a.size ?? a.width ?? ge.width, c = a.size ?? a.height ?? ge.height, i = a.aliases?.filter((d) => typeof d == "string" && d.trim() !== "").map((d) => `lucide-${d}`) ?? [], u = [...a.name ? [`lucide-${a.name}`] : [], ...i], y = r.className?.split(" ").filter(Boolean) ?? [], p = r.includeDefaultClasses === !1 ? Ue(...y) : Ue("lucide", ...u, ...y), f = r.absoluteStrokeWidth ? Number(r.strokeWidth ?? ge["stroke-width"]) * Number(a.size ?? a.width ?? ge.width) / Number(r.size ?? r.width ?? ge.width) : r.strokeWidth ?? ge["stroke-width"];
  return [
    "svg",
    {
      ...Object.entries(ge).reduce((d, [_, A]) => (d[o(_)] = A, d), {}),
      ..."color" in r && r.color && {
        [o("stroke")]: r.color
      },
      ..."size" in r && Oe(r.size) && {
        [o("width")]: r.size,
        [o("height")]: r.size
      },
      ..."width" in r && Oe(r.width) && {
        [o("width")]: r.width
      },
      ..."height" in r && Oe(r.height) && {
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
    a.node.map((d) => {
      const [_, A, E] = d, L = r.nonScalingStroke ? { [o("vector-effect")]: "non-scaling-stroke", ...A } : A;
      return E ? [_, L, E] : [_, L];
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
  return Ln(a, {
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
const Wn = (a) => {
  for (const r in a)
    if (r.startsWith("aria-") || r === "role" || r === "title")
      return !0;
  return !1;
}, qn = hn({}), Mn = () => un(qn), Tn = ft(
  ({
    color: a,
    size: r,
    width: n,
    height: o,
    strokeWidth: s,
    absoluteStrokeWidth: c,
    nonScalingStroke: i,
    className: u = "",
    children: y,
    iconNode: p = [],
    icon: f = {
      node: p,
      aliases: [],
      size: 24
    },
    ...h
  }, d) => {
    const {
      size: _ = 24,
      strokeWidth: A = 2,
      absoluteStrokeWidth: E = !1,
      nonScalingStroke: L = !1,
      color: S = "currentColor",
      className: I = ""
    } = Mn() ?? {}, J = !!y || Wn(h), [z, ee, j = []] = Sn(f, {
      color: a ?? S,
      width: n ?? r ?? _,
      height: o ?? r ?? _,
      strokeWidth: s ?? A,
      absoluteStrokeWidth: c ?? E,
      nonScalingStroke: i ?? L,
      className: Ue(I, u),
      hasA11yProp: J,
      attributes: h
    });
    return je(
      z,
      {
        ref: d,
        ...ee
      },
      [
        ...j.map(([b, C]) => je(b, C)),
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
function F(a, r = [], n = []) {
  const o = typeof a == "string" ? xn(a, r, n) : a, s = ft(
    ({ className: c, ...i }, u) => je(Tn, {
      ref: u,
      icon: o,
      className: c,
      ...i
    })
  );
  return o.name && (s.displayName = Dn(o.name)), s;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const At = {
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
At.node;
const Je = F(At);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const xt = {
  name: "calendar-plus",
  size: 24,
  node: [
    ["path", { d: "M16 18h6", key: "987eiv" }],
    ["path", { d: "M16 2v3", key: "otl347" }],
    ["path", { d: "M19 15v6", key: "10aioa" }],
    ["path", { d: "M21 11.5V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h8.3", key: "jgwkxf" }],
    ["path", { d: "M3 9h18", key: "1pudct" }],
    ["path", { d: "M8 2v3", key: "1ioesn" }]
  ]
};
xt.node;
const Nt = F(xt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Dt = {
  name: "chevron-left",
  size: 24,
  node: [["path", { d: "m15 18-6-6 6-6", key: "1wnfg3" }]]
};
Dt.node;
const $n = F(Dt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Lt = {
  name: "chevron-right",
  size: 24,
  node: [["path", { d: "m9 18 6-6-6-6", key: "mthhwq" }]]
};
Lt.node;
const St = F(Lt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Wt = {
  name: "clock",
  size: 24,
  node: [
    ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
    ["path", { d: "M12 6v6l4 2", key: "mmk7yg" }]
  ]
};
Wt.node;
const Ge = F(Wt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const qt = {
  name: "copy",
  size: 24,
  node: [
    ["rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2", key: "17jyea" }],
    ["path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2", key: "zix9uf" }]
  ]
};
qt.node;
const En = F(qt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Mt = {
  name: "download",
  size: 24,
  node: [
    ["path", { d: "M12 15V3", key: "m9g1x1" }],
    ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
    ["path", { d: "m7 10 5 5 5-5", key: "brsn70" }]
  ]
};
Mt.node;
const Fn = F(Mt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Tt = {
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
Tt.node;
const Pn = F(Tt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const $t = {
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
$t.node;
const dt = F($t);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Et = {
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
Et.node;
const Ft = F(Et);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Pt = {
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
Pt.node;
const Se = F(Pt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Bt = {
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
Bt.node;
const Bn = F(Bt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ht = {
  name: "log-in",
  size: 24,
  node: [
    ["path", { d: "m10 17 5-5-5-5", key: "1bsop3" }],
    ["path", { d: "M15 12H3", key: "6jk70r" }],
    ["path", { d: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4", key: "u53s6r" }]
  ]
};
Ht.node;
const Hn = F(Ht);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ot = {
  name: "log-out",
  size: 24,
  node: [
    ["path", { d: "m16 17 5-5-5-5", key: "1bji2h" }],
    ["path", { d: "M21 12H9", key: "dn1m92" }],
    ["path", { d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", key: "1uf3rs" }]
  ]
};
Ot.node;
const On = F(Ot);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const It = {
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
It.node;
const et = F(It);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const zt = {
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
zt.node;
const jt = F(zt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Yt = {
  name: "plus",
  size: 24,
  node: [
    ["path", { d: "M5 12h14", key: "1ays0h" }],
    ["path", { d: "M12 5v14", key: "s699le" }]
  ]
};
Yt.node;
const ye = F(Yt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Vt = {
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
Vt.node;
const Ke = F(Vt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ut = {
  name: "repeat",
  size: 24,
  node: [
    ["path", { d: "m17 2 4 4-4 4", key: "nntrym" }],
    ["path", { d: "M3 11v-1a4 4 0 0 1 4-4h14", key: "84bu3i" }],
    ["path", { d: "m7 22-4-4 4-4", key: "1wqhfi" }],
    ["path", { d: "M21 13v1a4 4 0 0 1-4 4H3", key: "1rx37r" }]
  ]
};
Ut.node;
const Jt = F(Ut);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Gt = {
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
Gt.node;
const In = F(Gt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Kt = {
  name: "users",
  size: 24,
  node: [
    ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
    ["path", { d: "M16 3.128a4 4 0 0 1 0 7.744", key: "16gr8j" }],
    ["path", { d: "M22 21v-2a4 4 0 0 0-3-3.87", key: "kshegd" }],
    ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }]
  ]
};
Kt.node;
const Xt = F(Kt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Zt = {
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
Zt.node;
const Qt = F(Zt), k = "seal_hrms.my_desk.api.", v = {
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
  compensatoryList: `${k}compensatory_list`,
  compensatoryOptions: `${k}compensatory_options`,
  compensatoryRecord: `${k}compensatory_record`,
  requestCompensatoryLeave: `${k}request_compensatory_leave`,
  compensatoryAction: `${k}compensatory_action`,
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
function zn(a) {
  return `/api/method/${v.payslipPdf}?name=${encodeURIComponent(a)}`;
}
function fe(a) {
  return a ? e("{0} will approve it.", [a]) : e("Nobody approves this yet. Ask HR to set your approver.");
}
function jn(a, r) {
  return a === null ? fe(r) : r ? e("{0} days. {1} will approve it.", [String(a), r]) : e("{0} days. Nobody approves this yet. Ask HR to set your approver.", [String(a)]);
}
function N() {
  const a = ce();
  return xe((r) => a.navigate(r), [a]);
}
const Yn = yn(
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
function Vn(a) {
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
  return a ? /* @__PURE__ */ t(fn, { status: a, label: Vn(a), toneOf: Yn }) : null;
}
const Un = 864e5;
function en(a) {
  const [r, n, o] = a.split("-").map(Number);
  return Date.UTC(r, n - 1, o);
}
function Jn(a) {
  return new Date(a).toISOString().slice(0, 10);
}
function we(a, r) {
  return Jn(en(a) + r * Un);
}
function tt(a) {
  const r = (new Date(en(a)).getUTCDay() + 6) % 7;
  return we(a, -r);
}
function U(a = /* @__PURE__ */ new Date()) {
  const r = (n) => String(n).padStart(2, "0");
  return `${a.getFullYear()}-${r(a.getMonth() + 1)}-${r(a.getDate())}`;
}
function Xe(a) {
  return Array.from({ length: 7 }, (r, n) => we(a, n));
}
function Ae(a) {
  const r = typeof a == "number" ? a : Number.parseFloat(String(a ?? ""));
  return Number.isFinite(r) && r > 0 ? Math.round(r * 100) / 100 : 0;
}
function tn(a, r) {
  return Math.round(a.reduce((n, o) => n + Ae(o.hours[r]), 0) * 100) / 100;
}
function Gn(a) {
  return Math.round(Xe("2000-01-03").reduce((r, n, o) => r + tn(a, o), 0) * 100) / 100;
}
function ut(a, r) {
  return { row: a.reduce((o, s) => Math.max(o, s.row), 0) + 1, activity_type: r, description: "", is_billable: 0, hours: [0, 0, 0, 0, 0, 0, 0] };
}
function Kn(a) {
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
function Xn(a, r, n, o) {
  return a.map((s) => s.row === r ? { ...s, hours: s.hours.map((c, i) => Ae(i === n ? o : c)) } : s);
}
function Zn(a) {
  return a.filter((r) => r.hours.some((n) => Ae(n) > 0) || (r.description ?? "").trim()).map((r, n) => ({ ...r, row: n + 1, hours: Array.from({ length: 7 }, (o, s) => Ae(r.hours[s])) }));
}
function Qn() {
  return "geolocation" in navigator ? new Promise(
    (a) => navigator.geolocation.getCurrentPosition(
      (r) => a({ latitude: r.coords.latitude, longitude: r.coords.longitude }),
      () => a(null),
      { enableHighAccuracy: !0, timeout: 1e4, maximumAge: 6e4 }
    )
  ) : Promise.resolve(null);
}
function ea() {
  const a = N(), r = B(), { data: n, isLoading: o, error: s, mutate: c } = x(v.checkinStatus), i = M(v.checkIn), [u, y] = T(!1), [p, f] = T(!1), h = async () => {
    if (!n) return;
    f(!1);
    let d = null;
    n.location && (y(!0), d = await Qn(), y(!1), f(!d));
    try {
      await i.run({ log_type: n.next, ...d ?? {} }), r.success(n.next === "IN" ? e("Checked in.") : e("Checked out.")), await c();
    } catch {
    }
  };
  return /* @__PURE__ */ t(re, { title: e("Check-in"), onBack: () => a(""), loading: o, error: s, onRetry: c, children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
    n.offered ? /* @__PURE__ */ m(de, { children: [
      i.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: i.errorMessage }),
      p && /* @__PURE__ */ t(D, { tone: "warning", children: e("Your phone did not share where you are. Allow location for this site if HR needs it.") }),
      /* @__PURE__ */ m(w, { size: "lg", loading: u || i.loading, onClick: h, children: [
        n.next === "IN" ? /* @__PURE__ */ t(Hn, {}) : /* @__PURE__ */ t(On, {}),
        n.next === "IN" ? e("Check In") : e("Check Out")
      ] }),
      n.location && /* @__PURE__ */ m(K, { size: "sm", muted: !0, children: [
        /* @__PURE__ */ t(et, { "aria-hidden": !0, className: "mr-1 inline size-4" }),
        e("Where you are is recorded with each check-in, as HR asks.")
      ] })
    ] }) : /* @__PURE__ */ t(D, { tone: "info", children: e("HR has not turned on checking in from the phone.") }),
    /* @__PURE__ */ t(O, { title: e("Today"), children: n.today.length === 0 ? /* @__PURE__ */ t(K, { muted: !0, children: e("No check-ins today yet. Clock-ins on the office device show here too.") }) : /* @__PURE__ */ t(W, { divided: !0, children: n.today.map((d) => /* @__PURE__ */ t(
      q,
      {
        primary: d.log_type === "IN" ? e("In") : e("Out"),
        secondary: d.device_id ? e("{0} · {1}", [Re(d.time), d.device_id]) : Re(d.time)
      },
      d.name
    )) }) })
  ] }) });
}
function ta() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.attendanceRequests);
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Attendance Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.attendanceNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("New Request")
      ] }),
      children: c && !r?.attendance.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(et, {}), title: e("No attendance requests"), description: e("Ask for days you worked from home or on duty elsewhere to count as attended.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r?.attendance ?? []).map((i) => /* @__PURE__ */ t(
        q,
        {
          primary: i.reason === "Work From Home" ? e("Work From Home") : e("On Duty"),
          secondary: e("{0} to {1}", [g(i.from_date), g(i.to_date)]),
          action: /* @__PURE__ */ t($, { value: i.docstatus === 1 ? "Approved" : i.docstatus === 2 ? "Cancelled" : "Open" }),
          onClick: () => a(l.attendanceRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function na() {
  const a = N(), r = B(), n = M(v.requestAttendance), o = ue(() => ae.object({ from_date: ke(() => e("From Date")), to_date: ke(() => e("To Date")), reason: ne(() => e("Reason")) }).loose(), []), s = he({
    schema: o,
    defaultValues: { from_date: U(), to_date: U(), reason: "Work From Home", explanation: "", half_day: !1 }
  }), c = s.watch("from_date");
  return /* @__PURE__ */ t(re, { title: e("New Attendance Request"), onBack: () => a(l.attendance), children: /* @__PURE__ */ m(
    me,
    {
      form: s,
      onSubmit: async (i) => {
        const u = await n.run({ ...i, half_day: i.half_day ? 1 : 0 });
        r.success(e("Request sent to HR.")), a(l.attendanceRecord(u));
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
        /* @__PURE__ */ t(oe, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(oe, { name: "to_date", label: e("To Date"), required: !0, minDate: c || void 0 }),
        /* @__PURE__ */ t(qe, { name: "half_day", label: e("Half Day") }),
        /* @__PURE__ */ t(H, { name: "explanation", label: e("Explanation"), multiline: !0, rows: 3 }),
        /* @__PURE__ */ t(pe, { submitLabel: e("Send Request"), onCancel: () => a(l.attendance) })
      ]
    }
  ) });
}
function ht({ doctype: a }) {
  const r = N(), n = se(X().name), { data: o, isLoading: s, error: c, mutate: i } = x(v.attendanceRecord, { doctype: a, name: n }), u = a === "Shift Request";
  return /* @__PURE__ */ t(
    Q,
    {
      title: u ? e("Shift Request") : e("Attendance Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t($, { value: u ? o.status : o.docstatus === 1 ? "Approved" : "Open" }),
      onBack: () => r(u ? l.shifts : l.attendance),
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ t(
        V,
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
function aa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.attendanceRequests);
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Shift Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.shiftNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("New Request")
      ] }),
      children: c && !r?.shifts.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Jt, {}), title: e("No shift requests"), description: e("Ask to work a different shift for some days.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r?.shifts ?? []).map((i) => /* @__PURE__ */ t(
        q,
        {
          primary: i.shift_type,
          secondary: i.to_date ? e("{0} to {1}", [g(i.from_date), g(i.to_date)]) : e("From {0}", [g(i.from_date)]),
          action: /* @__PURE__ */ t($, { value: i.status }),
          onClick: () => a(l.shiftRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function oa() {
  const a = N(), r = B(), n = x(v.attendanceOptions), o = M(v.requestShift), s = ue(() => ae.object({ shift_type: ne(() => e("Shift Type")), from_date: ke(() => e("From Date")) }).loose(), []), c = he({ schema: s, defaultValues: { shift_type: "", from_date: U(), to_date: "" } });
  return /* @__PURE__ */ m(re, { title: e("New Shift Request"), onBack: () => a(l.shifts), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    n.data && /* @__PURE__ */ t(D, { tone: n.data.has_shift_approver ? "info" : "warning", children: fe(n.data.has_shift_approver ? n.data.shift_approver_name : null) }),
    /* @__PURE__ */ m(
      me,
      {
        form: c,
        onSubmit: async (i) => {
          const u = await o.run({ shift_type: i.shift_type, from_date: i.from_date, to_date: i.to_date || void 0 });
          r.success(e("Request sent to {0}.", [n.data?.shift_approver_name ?? e("your shift approver")])), a(l.shiftRecord(u));
        },
        children: [
          /* @__PURE__ */ t(le, { name: "shift_type", label: e("Shift Type"), required: !0, options: (n.data?.shift_types ?? []).map((i) => ({ value: i, label: i })) }),
          /* @__PURE__ */ t(oe, { name: "from_date", label: e("From Date"), required: !0 }),
          /* @__PURE__ */ t(oe, { name: "to_date", label: e("To Date"), hint: e("Leave empty if the shift carries on.") }),
          /* @__PURE__ */ t(pe, { submitLabel: e("Send Request"), onCancel: () => a(l.shifts) })
        ]
      }
    )
  ] });
}
function ra(a) {
  return { show: !!a?.needed, standInRequired: !!a?.needed && !!a?.required };
}
function ia(a, r) {
  const n = a.filter((c) => c.work_date), o = new Set(n.map((c) => c.work_date)), s = r.filter((c) => !o.has(c.work_date)).map((c) => ({ work_date: c.work_date, hours: c.hours, work_done: "" }));
  return [...n, ...s].sort((c, i) => c.work_date.localeCompare(i.work_date));
}
function sa(a) {
  if (a.change === "Mobile Money") return a.mobile_no?.trim() ? [] : ["mobile_no"];
  const r = ["bank", "bank_account_no", "account_name"].filter((n) => !a[n]?.trim());
  return a.evidence ? r : [...r, "evidence"];
}
function la(a, r, n) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(a) || !/^\d{4}-\d{2}-\d{2}$/.test(r || a)) return null;
  const o = Date.UTC(+a.slice(0, 4), +a.slice(5, 7) - 1, +a.slice(8, 10)), s = r || a, c = Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  if (c < o) return null;
  const i = Math.round((c - o) / 864e5) + 1;
  return n ? i - 0.5 : i;
}
function ca(a, r) {
  return {
    itinerary: a.filter((n) => n.travel_from.trim() || n.travel_to.trim()),
    costings: r.filter((n) => n.expense_type || (n.total_amount ?? 0) > 0)
  };
}
function da(a) {
  return a.work_from_date === a.work_end_date ? g(a.work_from_date) : e("{0} to {1}", [g(a.work_from_date), g(a.work_end_date)]);
}
function ua() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.compensatoryList);
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Compensatory Leave"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.compensatoryNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("New Request")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(
        Z,
        {
          icon: /* @__PURE__ */ t(Nt, {}),
          title: e("No compensatory leave requests"),
          description: e("Worked on a public holiday or your day off? Ask for leave in return.")
        }
      ) : /* @__PURE__ */ t(W, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        q,
        {
          primary: i.leave_type,
          secondary: e("{0} · {1} days worked", [da(i), String(i.days)]),
          action: /* @__PURE__ */ t($, { value: i.state }),
          onClick: () => a(l.compensatoryRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function ha() {
  const a = N(), r = B(), n = x(v.compensatoryOptions), o = M(v.requestCompensatoryLeave), s = ue(
    () => ae.object({
      leave_type: ne(() => e("Leave Type")),
      work_from_date: ke(() => e("Work From Date")),
      work_end_date: ke(() => e("Work End Date")),
      reason: ne(() => e("Reason"))
    }).loose(),
    []
  ), c = U(), i = he({
    schema: s,
    defaultValues: { leave_type: "", work_from_date: c, work_end_date: c, half_day: !1, half_day_date: "", reason: "" }
  }), [u, y, p] = [i.watch("work_from_date"), i.watch("work_end_date"), i.watch("half_day")], f = la(u, y, p), h = n.data?.leave_types ?? [];
  return /* @__PURE__ */ t(re, { title: e("New Compensatory Leave Request"), onBack: () => a(l.compensatory), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: n.data && h.length === 0 ? /* @__PURE__ */ t(
    Z,
    {
      icon: /* @__PURE__ */ t(Se, {}),
      title: e("Claim it as time off in lieu"),
      description: e("Your organisation gives time off for extra work through time off in lieu claims."),
      action: /* @__PURE__ */ t(w, { onClick: () => a(l.toilNew), children: e("Claim Time Off") })
    }
  ) : /* @__PURE__ */ m(de, { children: [
    n.data && /* @__PURE__ */ t(D, { tone: n.data.workflow || n.data.approver_name ? "info" : "warning", children: n.data.workflow ? e("Your organisation's approval steps decide it.") : fe(n.data.approver_name) }),
    o.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: o.errorMessage }),
    /* @__PURE__ */ m(
      me,
      {
        form: i,
        onSubmit: async (d) => {
          const _ = await o.run({
            leave_type: d.leave_type,
            work_from_date: d.work_from_date,
            work_end_date: d.work_end_date || d.work_from_date,
            reason: d.reason,
            half_day: d.half_day ? 1 : 0,
            half_day_date: d.half_day ? d.half_day_date || d.work_from_date : void 0
          });
          r.success(_.state === "Waiting for Approval" ? e("Request sent.") : e("Request saved.")), a(l.compensatoryRecord(_.name));
        },
        children: [
          /* @__PURE__ */ t(le, { name: "leave_type", label: e("Leave Type"), required: !0, options: h.map((d) => ({ value: d, label: d })) }),
          /* @__PURE__ */ t(oe, { name: "work_from_date", label: e("Work From Date"), required: !0, hint: e("The first holiday or day off you worked.") }),
          /* @__PURE__ */ t(oe, { name: "work_end_date", label: e("Work End Date"), required: !0, minDate: u || void 0 }),
          /* @__PURE__ */ t(qe, { name: "half_day", label: e("Half Day") }),
          p && u && y && u !== y && /* @__PURE__ */ t(oe, { name: "half_day_date", label: e("Half Day Date"), minDate: u, maxDate: y }),
          /* @__PURE__ */ t(H, { name: "reason", label: e("Reason"), required: !0, multiline: !0, rows: 3, hint: e("What you worked on, so your approver can confirm it.") }),
          f !== null && /* @__PURE__ */ t(K, { muted: !0, children: e("{0} days of leave if approved.", [String(f)]) }),
          /* @__PURE__ */ t(pe, { submitLabel: e("Send Request"), onCancel: () => a(l.compensatory) })
        ]
      }
    )
  ] }) });
}
function ma() {
  const a = N(), r = B(), n = se(X().name), { data: o, isLoading: s, error: c, mutate: i } = x(v.compensatoryRecord, { name: n }), u = M(v.compensatoryAction), [y, p] = T(!1);
  return /* @__PURE__ */ m(
    Q,
    {
      title: e("Compensatory Leave Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t($, { value: o.state }),
      onBack: () => a(l.compensatory),
      actions: o?.can_withdraw ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => p(!0), children: e("Withdraw") }) : void 0,
      loading: s,
      error: c,
      onRetry: i,
      children: [
        o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
          u.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: u.errorMessage }),
          o.mine && o.state === "Waiting for Approval" && /* @__PURE__ */ t(D, { tone: "info", children: fe(o.approver_name) }),
          o.mine && o.state === "Rejected" && /* @__PURE__ */ t(D, { tone: "warning", children: e("Not approved. Withdraw it, or ask your approver if something has changed.") }),
          /* @__PURE__ */ t(
            V,
            {
              items: [
                { label: e("Leave Type"), value: o.leave_type },
                { label: e("Work From Date"), value: g(o.work_from_date) },
                { label: e("Work End Date"), value: g(o.work_end_date) },
                { label: e("Half Day Date"), value: o.half_day && o.half_day_date ? g(o.half_day_date) : null, hideWhenEmpty: !0 },
                { label: e("Days"), value: String(o.days) },
                { label: e("Approver"), value: o.approver_name, hideWhenEmpty: !0 },
                { label: e("Reason"), value: o.reason, hideWhenEmpty: !0, full: !0 },
                { label: e("Decision Note"), value: o.note, hideWhenEmpty: !0, full: !0 }
              ]
            }
          ),
          !o.mine && o.state === "Waiting for Approval" && /* @__PURE__ */ t(K, { muted: !0, children: e("Decide this request from Approvals.") })
        ] }),
        /* @__PURE__ */ t(
          Qe,
          {
            open: y,
            onClose: () => p(!1),
            title: e("Withdraw this request?"),
            confirmLabel: e("Withdraw"),
            destructive: !0,
            onConfirm: async () => {
              await u.run({ name: n, action: "Withdraw" }), r.success(e("Request withdrawn.")), a(l.compensatory);
            },
            children: e("It is deleted, and nobody will act on it.")
          }
        )
      ]
    }
  );
}
function Ie(a, r, n) {
  return /* @__PURE__ */ t(W, { divided: !0, children: a.map((o) => /* @__PURE__ */ t(
    q,
    {
      primary: r ? e("Covered by {0}", [o.stand_in]) : o.employee_name,
      secondary: e("{0} to {1}", [g(o.leave_from), g(o.leave_to)]),
      action: /* @__PURE__ */ t($, { value: o.waiting_for_me ? "Pending" : o.status }),
      onClick: () => n(l.handover(o.name))
    },
    o.name
  )) });
}
function pa() {
  const a = N(), [r, n] = T("to_answer"), { data: o, isLoading: s, error: c, mutate: i, hasLoaded: u } = x(v.cover), y = (p, f) => /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Xt, {}), title: p, description: f });
  return /* @__PURE__ */ m(ie, { title: e("Cover"), onBack: () => a(""), loading: s, error: c, onRetry: i, children: [
    /* @__PURE__ */ t(
      vn,
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
    /* @__PURE__ */ t(Be, { id: "to_answer", value: r, children: u && !o?.to_answer.length ? y(e("Nobody has asked you to cover"), e("When a colleague names you as their stand-in, it shows here for you to agree or decline.")) : Ie(o?.to_answer ?? [], !1, a) }),
    /* @__PURE__ */ t(Be, { id: "covering", value: r, children: u && !o?.covering.length ? y(e("You are not covering anyone now"), e("Work you agreed to cover shows here while the person is away.")) : Ie(o?.covering ?? [], !1, a) }),
    /* @__PURE__ */ t(Be, { id: "mine", value: r, children: u && !o?.mine.length ? y(e("No handovers of your own"), e("When you apply for leave, the handover you send shows here.")) : Ie(o?.mine ?? [], !0, a) })
  ] });
}
function ya() {
  const a = N(), r = B(), n = se(X().name), { data: o, isLoading: s, error: c, mutate: i } = x(v.handoverRecord, { name: n }), u = M(v.respond), y = M(v.respondAuthority), p = M(v.addNote), f = M(v.returnNote), h = M(v.returnWork), [d, _] = T(null), [A, E] = T(""), [L, S] = T(!1), [I, J] = T(!1), [z, ee] = T(null), j = async (C, Fe) => {
    J(!0), ee(null);
    try {
      await C(), r.success(Fe), _(null), E(""), await i();
    } catch (ve) {
      ee(ve);
    } finally {
      J(!1);
    }
  }, b = o && o.can_answer ? /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(w, { variant: "outline", onClick: () => _({ kind: "decline" }), children: e("Decline") }),
    /* @__PURE__ */ t(w, { loading: I, onClick: () => j(() => u.run({ name: n, answer: "Accepted" }), e("You agreed to cover this.")), children: e("Accept") })
  ] }) : o && o.can_return ? /* @__PURE__ */ t(w, { onClick: () => S(!0), children: e("I'm Back") }) : void 0;
  return /* @__PURE__ */ m(
    Q,
    {
      title: o ? o.is_owner ? e("My Handover") : e("Cover for {0}", [o.employee_name]) : e("Handover"),
      subtitle: o && e("{0} to {1}", [g(o.leave_from), g(o.leave_to)]),
      meta: o && /* @__PURE__ */ t($, { value: o.status }),
      onBack: () => a(l.cover),
      actions: b,
      loading: s,
      error: c,
      onRetry: i,
      children: [
        o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
          z ? /* @__PURE__ */ t(D, { tone: "error", children: u.errorMessage || y.errorMessage || h.errorMessage || e("That did not go through. Try again.") }) : null,
          /* @__PURE__ */ t(
            V,
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
          /* @__PURE__ */ t(O, { title: e("Work"), children: o.work.length === 0 ? /* @__PURE__ */ t(K, { muted: !0, children: e("No work items were handed over; the notes say what to look after.") }) : /* @__PURE__ */ t(W, { divided: !0, children: o.work.map((C) => /* @__PURE__ */ t(
            q,
            {
              primary: C.description,
              secondary: [C.covered_by, C.due_date ? e("Due {0}", [g(C.due_date)]) : "", C.notes ?? ""].filter(Boolean).join(" · "),
              action: C.mine && o.status === "Active" ? /* @__PURE__ */ t(w, { variant: "ghost", onClick: () => _({ kind: "note", row: C.row, text: C.notes ?? "" }), children: e("Leave a Note") }) : C.progress || C.acceptance ? /* @__PURE__ */ t($, { value: C.progress || C.acceptance }) : void 0
            },
            C.row
          )) }) }),
          o.approvals.length > 0 && /* @__PURE__ */ t(O, { title: e("Approvals"), children: /* @__PURE__ */ t(W, { divided: !0, children: o.approvals.map((C) => /* @__PURE__ */ t(
            q,
            {
              primary: C.label,
              secondary: C.covered_by,
              action: C.mine && o.can_answer && C.acceptance === "Pending" ? /* @__PURE__ */ m("div", { className: "flex gap-1", children: [
                /* @__PURE__ */ t(w, { variant: "ghost", onClick: () => _({ kind: "decline-approval", row: C.row }), children: e("Decline") }),
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
          o.is_stand_in && o.status === "Active" && /* @__PURE__ */ t(w, { variant: "outline", onClick: () => _({ kind: "return-note" }), children: e("Note for Return") })
        ] }),
        /* @__PURE__ */ t(
          bt,
          {
            open: !!d,
            onClose: () => _(null),
            title: d?.kind === "note" ? e("Leave a Note") : d?.kind === "return-note" ? e("Note for Return") : e("Decline"),
            description: d?.kind === "note" ? e("What you did on this piece of work, for when they are back.") : d?.kind === "return-note" ? e("What they should know on their first day back.") : e("Say why you cannot cover it, so they can ask someone else."),
            actions: /* @__PURE__ */ m(de, { children: [
              /* @__PURE__ */ t(w, { variant: "outline", onClick: () => _(null), children: e("Cancel") }),
              /* @__PURE__ */ t(
                w,
                {
                  loading: I,
                  disabled: !(d?.kind === "note" ? d.text : A).trim(),
                  onClick: () => {
                    d && (d.kind === "decline" ? j(() => u.run({ name: n, answer: "Declined", reason: A }), e("You declined.")) : d.kind === "decline-approval" ? j(() => y.run({ name: n, row: d.row, answer: "Declined", reason: A }), e("You declined.")) : d.kind === "note" ? j(() => p.run({ name: n, row: d.row, note: d.text }), e("Note saved.")) : j(() => f.run({ name: n, note: A }), e("Note saved.")));
                  },
                  children: d?.kind === "decline" || d?.kind === "decline-approval" ? e("Decline") : e("Save Note")
                }
              )
            ] }),
            children: /* @__PURE__ */ t(
              _n,
              {
                "aria-label": e("Note"),
                rows: 4,
                value: d?.kind === "note" ? d.text : A,
                onChange: (C) => d?.kind === "note" ? _({ ...d, text: C.target.value }) : E(C.target.value)
              }
            )
          }
        ),
        /* @__PURE__ */ t(
          Qe,
          {
            open: L,
            onClose: () => S(!1),
            title: e("Take your work back now?"),
            confirmLabel: e("I'm Back"),
            onConfirm: async () => {
              await h.run({ name: n }), r.success(e("Your work is back with you.")), await i();
            },
            children: e("Everything your stand-in was covering comes back to you, and they stop approving in your place.")
          }
        )
      ]
    }
  );
}
function fa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s } = x(v.home), c = l.week(tt(U())), i = [
    { label: e("Leave"), hint: e("Apply, and see what you asked for"), path: l.leave, icon: /* @__PURE__ */ t(Je, {}) },
    { label: e("Cover"), hint: e("Handovers to answer and work you cover"), path: l.cover, icon: /* @__PURE__ */ t(Xt, {}) },
    { label: e("Time Off in Lieu"), hint: e("Claim extra hours as time off"), path: l.toil, icon: /* @__PURE__ */ t(Se, {}) },
    { label: e("Timesheets"), hint: e("Your week, day by day"), path: l.timesheet, icon: /* @__PURE__ */ t(Ge, {}) },
    { label: e("Expense Claims"), hint: e("Claims and receipts"), path: l.expenses, icon: /* @__PURE__ */ t(Ke, {}) },
    { label: e("Advances"), hint: e("Money paid ahead and what is left to settle"), path: l.advances, icon: /* @__PURE__ */ t(Ft, {}) },
    { label: e("Payslips"), hint: e("Your pay, month by month"), path: l.pay, icon: /* @__PURE__ */ t(Qt, {}) },
    { label: e("Attendance Requests"), hint: e("Days worked away from the office"), path: l.attendance, icon: /* @__PURE__ */ t(et, {}) },
    { label: e("Shift Requests"), hint: e("Ask to work another shift"), path: l.shifts, icon: /* @__PURE__ */ t(Jt, {}) },
    { label: e("Travel Requests"), hint: e("Trips for work, approved by your line manager"), path: l.travel, icon: /* @__PURE__ */ t(jt, {}) },
    { label: e("My Details"), hint: e("Contact, dependants and where you are paid"), path: l.me, icon: /* @__PURE__ */ t(Bn, {}) }
  ];
  return r?.compensatory && i.splice(3, 0, { label: e("Compensatory Leave"), hint: e("Leave in return for working a holiday or day off"), path: l.compensatory, icon: /* @__PURE__ */ t(Nt, {}) }), r?.checkin.offered && i.splice(4, 0, { label: e("Check-in"), hint: e("Check in and out from your phone"), path: l.checkIn, icon: /* @__PURE__ */ t(dt, {}) }), /* @__PURE__ */ t(gn, { title: e("Self Service"), subtitle: r?.employee.employee_name, loading: n, error: o, onRetry: s, children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
    r && r.balances.length > 0 && /* @__PURE__ */ t(Ct, { columns: 2, children: r.balances.map((u) => /* @__PURE__ */ t(Ye, { label: u.label, value: e("{0} days", [String(u.value)]), onClick: () => a(u.key.startsWith("toil") ? l.toil : l.leave) }, u.key)) }),
    /* @__PURE__ */ t(O, { title: e("Quick Actions"), children: /* @__PURE__ */ m("div", { className: "grid grid-cols-1 gap-2 sm:grid-cols-2", children: [
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.leaveNew), children: [
        /* @__PURE__ */ t(Je, {}),
        e("Apply for Leave")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.toilNew), children: [
        /* @__PURE__ */ t(Se, {}),
        e("Claim Time Off")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(c), children: [
        /* @__PURE__ */ t(Pn, {}),
        e("This Week's Timesheet")
      ] }),
      /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.expenseNew), children: [
        /* @__PURE__ */ t(Ke, {}),
        e("New Expense Claim")
      ] }),
      r?.checkin.offered && /* @__PURE__ */ m(w, { variant: "outline", onClick: () => a(l.checkIn), children: [
        /* @__PURE__ */ t(dt, {}),
        e("Check In")
      ] })
    ] }) }),
    r && r.in_flight.length > 0 && /* @__PURE__ */ t(O, { title: e("In Progress"), children: /* @__PURE__ */ t(W, { divided: !0, children: r.in_flight.map((u) => {
      const y = Rn(u.doctype);
      return /* @__PURE__ */ t(q, { primary: u.label, action: /* @__PURE__ */ t(be, { children: u.count }), onClick: y ? () => a(y) : void 0 }, u.key);
    }) }) }),
    /* @__PURE__ */ t(O, { title: e("Everything in Self Service"), children: /* @__PURE__ */ t(W, { divided: !0, children: i.map((u) => /* @__PURE__ */ t(q, { primary: u.label, secondary: u.hint, icon: u.icon, action: /* @__PURE__ */ t(St, { "aria-hidden": !0 }), onClick: () => a(u.path) }, u.path)) }) })
  ] }) });
}
const va = "seal-draft:", _a = 30, ga = 400;
function ka(a, r, n) {
  return `${va}${a}:${r}:${n}`;
}
function nt() {
  try {
    return typeof window < "u" ? window.localStorage : null;
  } catch {
    return null;
  }
}
function Ze(a, r = Date.now()) {
  const n = nt();
  if (!n) return null;
  try {
    const o = n.getItem(a);
    if (!o) return null;
    const s = JSON.parse(o);
    if (!s || typeof s.saved != "number" || !("value" in s)) throw new Error("not a draft");
    return r - s.saved > _a * 864e5 ? (n.removeItem(a), null) : { value: s.value, saved: s.saved };
  } catch {
    try {
      n.removeItem(a);
    } catch {
    }
    return null;
  }
}
function wa(a, r, n = Date.now()) {
  const o = nt();
  if (!o) return !1;
  try {
    return o.setItem(a, JSON.stringify({ saved: n, value: r })), !0;
  } catch {
    return !1;
  }
}
function nn(a) {
  try {
    nt()?.removeItem(a);
  } catch {
  }
}
function Te(a, r, n) {
  const o = a && n ? ka(a, r, n) : null, [s, c] = T(() => o ? Ze(o) : null), i = Ce(null), u = Ce(o);
  _e(() => {
    u.current !== o && (u.current = o, c(o ? Ze(o) : null));
  }, [o]), _e(
    () => () => {
      i.current && clearTimeout(i.current);
    },
    []
  );
  const y = xe(
    (h) => {
      o && (i.current && clearTimeout(i.current), i.current = setTimeout(() => wa(o, h), ga));
    },
    [o]
  ), p = xe(() => {
    i.current && clearTimeout(i.current), i.current = null, o && nn(o), c(null);
  }, [o]), f = xe(() => c(null), []);
  return { key: o, restored: s, keep: y, clear: p, dismiss: f };
}
function $e(a) {
  return U(new Date(a));
}
function ba() {
  const a = N(), [r, n] = T("all"), { data: o, isLoading: s, error: c, mutate: i, hasLoaded: u } = x(v.leaveList), y = o ?? [], p = y.filter((h) => h.status === "Open" && h.docstatus === 0), f = r === "open" ? p : r === "decided" ? y.filter((h) => !p.includes(h)) : y;
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Leave"),
      onBack: () => a(""),
      loading: s,
      error: c,
      onRetry: i,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.leaveNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("Apply for Leave")
      ] }),
      toolbar: /* @__PURE__ */ t(
        kn,
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
      children: u && f.length === 0 ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Je, {}), title: e("No leave here"), description: e("Leave you apply for shows here until it is decided, and after.") }) : /* @__PURE__ */ t(W, { divided: !0, children: f.map((h) => /* @__PURE__ */ t(
        q,
        {
          primary: h.leave_type,
          secondary: h.handover ? e("{0} to {1} · {2} days · covered by {3}", [g(h.from_date), g(h.to_date), String(h.total_leave_days), h.handover.stand_in]) : e("{0} to {1} · {2} days", [g(h.from_date), g(h.to_date), String(h.total_leave_days)]),
          action: /* @__PURE__ */ t($, { value: h.status }),
          onClick: () => a(l.leaveRecord(h.name))
        },
        h.name
      )) })
    }
  );
}
function Ca() {
  const a = N(), r = B(), [n] = vt(), o = ue(
    () => ae.object({
      leave_type: ne(() => e("Leave Type")),
      from_date: ke(() => e("From Date")),
      to_date: ke(() => e("To Date"))
    }),
    []
  ), s = () => ({ leave_type: n.get("type") ?? "", from_date: "", to_date: "", half_day: !1, description: "", stand_in: "", handover_notes: "", todos: [], approvals: [] }), c = he({ schema: o.passthrough(), defaultValues: s() }), i = Te(ce().user, "leave-application", "new"), [u, y] = T(null);
  _e(() => {
    i.restored?.value && !n.get("type") && (c.reset({ ...s(), ...i.restored.value }), y(i.restored.saved)), i.dismiss();
    const b = c.watch((C) => i.keep({ ...s(), ...C }));
    return () => b.unsubscribe();
  }, []);
  const p = () => {
    i.clear(), y(null), c.reset(s());
  }, [f, h, d, _] = c.watch(["leave_type", "from_date", "to_date", "half_day"]), A = !!(f && h && d), E = x(v.leaveOptions), L = x(v.leaveOptions, { leave_type: f, from_date: h, to_date: d, half_day: _ ? 1 : 0 }, { enabled: A }), S = { ...L, data: A ? L.data : void 0 }, I = x(v.colleagues, {}, { enabled: !!S.data?.handover.needed }), J = M(v.applyForLeave), z = ra(A ? S.data?.handover : void 0), ee = (S.data ?? E.data)?.leave_types.find((b) => b.name === f), j = async (b) => {
    if (z.standInRequired && !b.stand_in) return { errors: { stand_in: e("Your company asks for cover on this leave. Choose who will cover your work.") } };
    const C = await J.run({
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
  return /* @__PURE__ */ m(re, { title: e("Apply for Leave"), onBack: () => a(l.leave), loading: E.isLoading && !E.data, error: E.error, onRetry: E.mutate, children: [
    u !== null && /* @__PURE__ */ t(D, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: p, children: e("Start Again") }), children: e("You started this application on {0} and had not sent it.", [g($e(u))]) }),
    /* @__PURE__ */ m(me, { form: c, onSubmit: j, children: [
      /* @__PURE__ */ t(lt, { title: e("Leave"), children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          le,
          {
            name: "leave_type",
            label: e("Leave Type"),
            required: !0,
            options: (E.data?.leave_types ?? []).map((b) => ({
              value: b.name,
              label: b.name,
              description: b.left === null ? e("Unpaid") : e("{0} days left", [String(b.left)])
            })),
            hint: ee && ee.left !== null ? e("{0} days left", [String(ee.left)]) : void 0
          }
        ),
        /* @__PURE__ */ t(oe, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(oe, { name: "to_date", label: e("To Date"), required: !0, minDate: h || void 0 }),
        /* @__PURE__ */ t(qe, { name: "half_day", label: e("Half Day"), hint: e("Only the first day is a half day.") }),
        /* @__PURE__ */ t(H, { name: "description", label: e("Reason"), multiline: !0, rows: 3 }),
        A && S.data && /* @__PURE__ */ t(D, { tone: "info", children: jn(S.data.days, S.data.approver_name) })
      ] }) }),
      z.show && /* @__PURE__ */ t(
        lt,
        {
          title: e("Handover"),
          description: z.standInRequired ? e("Your company asks for cover on leave like this. Your stand-in is asked to agree before the leave is approved.") : e("Your company suggests arranging cover. You can leave this out."),
          children: /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
            /* @__PURE__ */ t(
              Pe,
              {
                name: "stand_in",
                label: e("Stand-in"),
                required: z.standInRequired,
                options: (I.data ?? []).map((b) => ({ value: b.name, label: b.employee_name })),
                hint: e("A colleague in your company who is not away at the same time.")
              }
            ),
            /* @__PURE__ */ t(H, { name: "handover_notes", label: e("Handover Notes"), multiline: !0, rows: 4, hint: e("What your stand-in needs to know.") }),
            (S.data?.work.length ?? 0) > 0 && /* @__PURE__ */ t(
              Pe,
              {
                name: "todos",
                multiple: !0,
                label: e("Work to Hand Over"),
                options: (S.data?.work ?? []).map((b) => ({ value: b.todo, label: b.description, description: b.due_date ? e("Due {0}", [g(b.due_date)]) : void 0 })),
                hint: e("Open items on your work list. Your stand-in gets them while you are away.")
              }
            ),
            (S.data?.approvals.length ?? 0) > 0 && /* @__PURE__ */ t(
              Pe,
              {
                name: "approvals",
                multiple: !0,
                label: e("Approvals to Hand Over"),
                options: (S.data?.approvals ?? []).map((b) => ({ value: b.authority, label: b.authority_label })),
                hint: e("Your stand-in approves these in your place, once they agree.")
              }
            )
          ] })
        }
      ),
      /* @__PURE__ */ t(pe, { submitLabel: e("Apply"), onCancel: () => a(l.leave) })
    ] })
  ] });
}
function Ra() {
  const a = N(), r = se(X().name), { data: n, isLoading: o, error: s, mutate: c } = x(v.leaveRecord, { name: r });
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
          V,
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
        n.handover ? /* @__PURE__ */ t(W, { divided: !0, children: /* @__PURE__ */ t(
          q,
          {
            primary: e("Handover to {0}", [n.handover.stand_in]),
            action: /* @__PURE__ */ t($, { value: n.handover.status }),
            onClick: () => a(l.handover(n.handover.name))
          }
        ) }) : /* @__PURE__ */ t(K, { muted: !0, children: e("No handover for this leave.") })
      ] })
    }
  );
}
class at extends Error {
  constructor() {
    super(...arguments);
    st(this, "name", "VerificationCancelled");
  }
}
function We(a, r = 0) {
  if (!a || typeof a != "object" || r > 3) return !1;
  const n = a;
  return n.exc_type === "VerificationNeeded" || typeof n.exception == "string" && n.exception.includes("VerificationNeeded") ? !0 : We(n.payload, r + 1) || We(n.original, r + 1);
}
async function ot(a, r) {
  try {
    return await a();
  } catch (n) {
    if (!We(n)) throw n;
    if (!await r()) throw new at();
    return a();
  }
}
function rt(a, r) {
  const n = ce(), o = We(a), [s, c] = T(!1), i = Ce(!1), u = async () => {
    c(!0);
    try {
      await n.verify() && await r();
    } finally {
      c(!1);
    }
  };
  return _e(() => {
    o && !i.current && (i.current = !0, u());
  }, [o]), { needed: o, busy: s, confirm: u, error: o ? void 0 : a };
}
function Ee({ what: a, busy: r, onConfirm: n }) {
  return /* @__PURE__ */ t(
    D,
    {
      tone: "info",
      role: "status",
      title: e("Confirm It Is You"),
      action: /* @__PURE__ */ t(w, { loading: r, onClick: n, children: e("Confirm") }),
      children: a
    }
  );
}
function Aa() {
  const a = N(), r = B(), { data: n, isLoading: o, error: s, mutate: c } = x(v.myDetails), i = M(v.updateMyContact), [u, y] = T(!1), [p, f] = T("");
  return /* @__PURE__ */ m(Q, { title: e("My Details"), subtitle: n?.employee.employee_name, onBack: () => a(""), loading: o, error: s, onRetry: c, children: [
    n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
      /* @__PURE__ */ t(
        V,
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
        O,
        {
          title: e("Contact"),
          action: n.has_contact ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => y(!0), children: e("Change Mobile Number") }) : void 0,
          children: [
            /* @__PURE__ */ t(V, { items: [{ label: e("Mobile No."), value: n.mobile_no ?? e("None yet") }] }),
            !n.has_contact && /* @__PURE__ */ t(K, { muted: !0, children: e("HR has not linked a contact to your record yet; ask them to.") })
          ]
        }
      ),
      /* @__PURE__ */ t(O, { title: e("Dependants and Beneficiaries"), children: n.dependants.length === 0 ? /* @__PURE__ */ t(K, { muted: !0, children: e("None recorded. HR records dependants and beneficiaries.") }) : /* @__PURE__ */ t(W, { divided: !0, children: n.dependants.map((h) => /* @__PURE__ */ t(q, { primary: h.full_name, secondary: [h.relationship, h.type, h.dob ? g(h.dob) : ""].filter(Boolean).join(" · ") }, h.name)) }) }),
      /* @__PURE__ */ m(
        O,
        {
          title: e("Payout Details"),
          subtitle: e("Where your pay goes. Only the last four digits are shown."),
          action: /* @__PURE__ */ t(w, { disabled: !!n.payout_request, onClick: () => a(l.payoutNew), children: e("Request a Change") }),
          children: [
            n.payout ? /* @__PURE__ */ t(
              V,
              {
                items: [
                  { label: e("Bank"), value: n.payout.bank ?? e("None") },
                  { label: e("Account No."), value: n.payout.account_no, hideWhenEmpty: !0 },
                  { label: e("Account Name"), value: n.payout.account_name, hideWhenEmpty: !0 },
                  { label: e("Mobile Money"), value: n.payout.mobile_no ?? e("None") }
                ]
              }
            ) : /* @__PURE__ */ t(xa, { onConfirmed: c }),
            n.payout_requests.length > 0 && /* @__PURE__ */ t(W, { divided: !0, children: n.payout_requests.map((h) => /* @__PURE__ */ t(
              q,
              {
                primary: h.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
                secondary: Re(h.creation),
                action: /* @__PURE__ */ t($, { value: h.status }),
                onClick: () => a(l.payoutRecord(h.name))
              },
              h.name
            )) })
          ]
        }
      )
    ] }),
    /* @__PURE__ */ t(
      bt,
      {
        open: u,
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
          i.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: i.errorMessage }),
          /* @__PURE__ */ t(Ne, { htmlFor: "new-mobile", children: e("New Mobile No.") }),
          /* @__PURE__ */ t(Ve, { id: "new-mobile", type: "tel", inputMode: "tel", autoComplete: "tel", value: p, onChange: (h) => f(h.target.value) })
        ] })
      }
    )
  ] });
}
function xa({ onConfirmed: a }) {
  const r = ce(), [n, o] = T(!1), s = async () => {
    o(!0);
    try {
      await r.verify() && await a();
    } finally {
      o(!1);
    }
  };
  return /* @__PURE__ */ t(Ee, { what: e("Your payout details show once you confirm it is you."), busy: n, onConfirm: s });
}
function Na() {
  const a = N(), r = ce(), n = B(), o = x(v.payoutOptions), s = M(v.requestPayoutChange), c = M(v.setPayoutEvidence), i = M(v.sendPayoutChange), u = he({
    defaultValues: { change: "Bank Account", bank: "", bank_account_no: "", branch_code: "", account_name: "", mobile_no: "", evidence: null, reason: "" }
  }), y = u.watch("change"), p = ue(
    () => ({ bank: e("Bank"), bank_account_no: e("Account No."), account_name: e("Account Name"), mobile_no: e("Mobile No."), evidence: e("Evidence") }),
    []
  ), f = async (h) => {
    const d = sa(h);
    if (d.length) return { errors: Object.fromEntries(d.map((A) => [A, e("{0} is needed.", [p[A]])])) };
    const _ = await s.run({
      change: h.change,
      bank: h.change === "Bank Account" ? h.bank : void 0,
      bank_account_no: h.change === "Bank Account" ? h.bank_account_no : void 0,
      branch_code: h.change === "Bank Account" ? h.branch_code : void 0,
      account_name: h.change === "Bank Account" ? h.account_name : void 0,
      mobile_no: h.change === "Mobile Money" ? h.mobile_no : void 0,
      reason: h.reason
    });
    if (h.change === "Bank Account" && h.evidence) {
      const A = await _t(h.evidence, { doctype: "Payout Change Request", docname: _, fieldname: "evidence", isPrivate: !0 });
      await c.run({ name: _, file_url: A.file_url });
    }
    try {
      await ot(() => i.run({ name: _ }), r.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it."));
    } catch (A) {
      if (!(A instanceof at)) throw A;
      n.info(e("Saved, not sent. Open it from My Details to send it."));
    }
    a(l.payoutRecord(_));
  };
  return /* @__PURE__ */ m(re, { title: e("Request a Change"), subtitle: e("Where your pay goes"), onBack: () => a(l.me), loading: o.isLoading, error: o.error, onRetry: o.mutate, children: [
    /* @__PURE__ */ t(D, { tone: "info", children: e("HR confirms every change before any pay goes there. We also tell your current number and email, in case this was not you.") }),
    /* @__PURE__ */ m(me, { form: u, onSubmit: f, children: [
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
        /* @__PURE__ */ t(le, { name: "bank", label: e("Bank"), required: !0, options: (o.data?.banks ?? []).map((h) => ({ value: h, label: h })) }),
        /* @__PURE__ */ t(H, { name: "bank_account_no", label: e("Account No."), required: !0 }),
        /* @__PURE__ */ t(H, { name: "branch_code", label: e("Branch") }),
        /* @__PURE__ */ t(H, { name: "account_name", label: e("Account Name"), required: !0, hint: e("As the bank has it. It must be in your own name.") }),
        /* @__PURE__ */ t(kt, { name: "evidence", label: e("Evidence"), required: !0, upload: !1, accept: "image/*,application/pdf", hint: e("A bank letter or the top of a statement, showing the account in your name.") })
      ] }) : /* @__PURE__ */ t(pn, { name: "mobile_no", label: e("Mobile No."), required: !0, hint: e("The number your pay should go to by mobile money.") }),
      /* @__PURE__ */ t(H, { name: "reason", label: e("Reason"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(pe, { submitLabel: e("Send to HR"), onCancel: () => a(l.me), dirtyHint: !1 })
    ] })
  ] });
}
function Da() {
  const a = N(), r = ce(), n = B(), o = se(X().name), { data: s, isLoading: c, error: i, mutate: u } = x(v.payoutRequestRecord, { name: o }), y = rt(i, u), p = M(v.sendPayoutChange), f = M(v.withdrawPayoutChange), [h, d] = T(!1), _ = async () => {
    try {
      await ot(() => p.run({ name: o }), r.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it.")), await u();
    } catch {
    }
  }, A = s?.mine && s.status === "Draft" ? /* @__PURE__ */ t(w, { loading: p.loading, onClick: _, children: e("Send to HR") }) : s?.mine && s.status === "Waiting for HR" ? /* @__PURE__ */ t(w, { variant: "outline", onClick: () => d(!0), children: e("Withdraw") }) : void 0;
  return /* @__PURE__ */ m(
    Q,
    {
      title: s?.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
      subtitle: o,
      meta: s && /* @__PURE__ */ t($, { value: s.status }),
      onBack: () => a(l.me),
      actions: A,
      loading: c,
      error: y.error,
      onRetry: u,
      children: [
        y.needed && /* @__PURE__ */ t(Ee, { what: e("This request shows once you confirm it is you."), busy: y.busy, onConfirm: y.confirm }),
        s && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
          p.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: p.errorMessage }),
          s.status === "Waiting for HR" && /* @__PURE__ */ t(D, { tone: "info", children: e("HR confirms it on the desk. You are told either way.") }),
          /* @__PURE__ */ t(
            V,
            {
              items: [
                { label: e("Bank"), value: s.bank, hideWhenEmpty: !0 },
                { label: e("Account No."), value: s.account_no, hideWhenEmpty: !0 },
                { label: e("Account Name"), value: s.account_name, hideWhenEmpty: !0 },
                { label: e("Mobile No."), value: s.mobile_no, hideWhenEmpty: !0 },
                { label: e("Provider"), value: s.provider, hideWhenEmpty: !0 },
                { label: e("Evidence"), value: s.change === "Bank Account" ? s.has_evidence ? e("Attached") : e("Missing") : null, hideWhenEmpty: !0 },
                { label: e("Sent On"), value: s.sent_on ? Re(s.sent_on) : null, hideWhenEmpty: !0 },
                { label: e("Effective From"), value: s.effective_from ? g(s.effective_from) : null, hideWhenEmpty: !0 },
                { label: e("Decision Note"), value: s.decision_note, hideWhenEmpty: !0, full: !0 },
                { label: e("Reason"), value: s.reason, hideWhenEmpty: !0, full: !0 }
              ]
            }
          )
        ] }),
        /* @__PURE__ */ t(
          Qe,
          {
            open: h,
            onClose: () => d(!1),
            title: e("Withdraw this request?"),
            confirmLabel: e("Withdraw"),
            destructive: !0,
            onConfirm: async () => {
              await f.run({ name: o }), n.success(e("Request withdrawn.")), await u();
            },
            children: e("HR will not act on it. Your pay keeps going where it goes now.")
          }
        )
      ]
    }
  );
}
function La() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.expenseList);
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Expense Claims"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.expenseNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("New Expense Claim")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Ke, {}), title: e("No expense claims yet"), description: e("Claim what you spent for work, with a photo of each receipt.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        q,
        {
          primary: P(i.total_claimed_amount, i.currency),
          secondary: g(i.posting_date || i.creation),
          action: /* @__PURE__ */ t($, { value: i.docstatus === 0 ? i.approval_status || "Draft" : i.status }),
          onClick: () => a(l.expenseRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function Sa() {
  const a = N(), r = B(), n = x(v.expenseOptions), o = M(v.claimExpenses), s = ue(
    () => ae.object({
      lines: ae.array(ae.object({ expense_type: ne(() => e("Expense Type")), amount: wt(() => e("Amount"), { min: 0.01 }) }).loose()).min(1)
    }).loose(),
    []
  ), c = () => ({ lines: [{ expense_date: U(), expense_type: "", amount: null, description: "" }], remark: "", receipts: [] }), i = he({ schema: s, defaultValues: c() }), u = Te(ce().user, "expense-claim", "new"), [y, p] = T(null);
  _e(() => {
    u.restored && Array.isArray(u.restored.value?.lines) && u.restored.value.lines.length && (i.reset({ ...c(), ...u.restored.value, receipts: [] }), p(u.restored.saved), u.dismiss());
    const d = i.watch((_) => u.keep({ lines: _.lines ?? [], remark: _.remark ?? "" }));
    return () => d.unsubscribe();
  }, []);
  const f = () => {
    u.clear(), p(null), i.reset(c());
  }, h = async (d) => {
    const _ = await o.run({ lines: JSON.stringify(d.lines), remark: d.remark });
    u.clear();
    const A = [];
    for (const E of d.receipts ?? [])
      try {
        await _t(E, { doctype: "Expense Claim", docname: _, isPrivate: !0 });
      } catch {
        A.push(E.name);
      }
    A.length ? r.warning(e("The claim was saved, but {0} receipts did not upload. Add them on a computer.", [String(A.length)])) : r.success(e("Claim sent to {0}.", [n.data?.approver_name ?? e("your expense approver")])), a(l.expenseRecord(_));
  };
  return /* @__PURE__ */ m(re, { title: e("New Expense Claim"), onBack: () => a(l.expenses), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    y !== null && /* @__PURE__ */ t(D, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: f, children: e("Start Again") }), children: e("You started this claim on {0}. Add the receipts again before you send it.", [g($e(y))]) }),
    n.data && /* @__PURE__ */ t(D, { tone: n.data.approver_name ? "info" : "warning", children: fe(n.data.approver_name) }),
    /* @__PURE__ */ m(me, { form: i, onSubmit: h, children: [
      /* @__PURE__ */ t(
        Le,
        {
          name: "lines",
          label: e("Expenses"),
          minRows: 1,
          addLabel: e("Add an Expense"),
          newRow: () => ({ expense_date: U(), expense_type: "", amount: null, description: "" }),
          renderRow: (d) => /* @__PURE__ */ m(de, { children: [
            /* @__PURE__ */ t(le, { name: d("expense_type"), label: e("Expense Type"), required: !0, options: (n.data?.types ?? []).map((_) => ({ value: _.name, label: _.name, description: _.description ?? void 0 })) }),
            /* @__PURE__ */ t(Me, { name: d("amount"), label: e("Amount ({0})", [n.data?.currency ?? ""]), required: !0, min: 0, step: 0.01 }),
            /* @__PURE__ */ t(oe, { name: d("expense_date"), label: e("Date"), maxDate: U() }),
            /* @__PURE__ */ t(H, { name: d("description"), label: e("Description") })
          ] })
        }
      ),
      /* @__PURE__ */ t(kt, { name: "receipts", label: e("Receipts"), multiple: !0, upload: !1, accept: "image/*,application/pdf", hint: e("Take a photo of each receipt, or choose a file. Only you, your approver and HR can open them.") }),
      /* @__PURE__ */ t(H, { name: "remark", label: e("Note"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(pe, { submitLabel: e("Send Claim"), onCancel: () => a(l.expenses) })
    ] })
  ] });
}
function Wa() {
  const a = N(), r = se(X().name), { data: n, isLoading: o, error: s, mutate: c } = x(v.expenseRecord, { name: r });
  return /* @__PURE__ */ t(
    Q,
    {
      title: n ? P(n.total_claimed_amount, n.currency) : e("Expense Claim"),
      subtitle: n && (n.mine ? r : n.employee_name),
      meta: n && /* @__PURE__ */ t($, { value: n.docstatus === 0 ? n.approval_status || "Draft" : n.status }),
      onBack: () => a(l.expenses),
      loading: o,
      error: s,
      onRetry: c,
      children: n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        /* @__PURE__ */ t(
          V,
          {
            items: [
              { label: e("Claimed"), value: P(n.total_claimed_amount, n.currency) },
              { label: e("Approved Amount"), value: n.docstatus === 1 ? P(n.total_sanctioned_amount, n.currency) : null, hideWhenEmpty: !0 },
              { label: e("Expense Approver"), value: n.approver_name, hideWhenEmpty: !0 },
              { label: e("Note"), value: n.remark, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(O, { title: e("Expenses"), children: /* @__PURE__ */ t(W, { divided: !0, children: n.expenses.map((i, u) => /* @__PURE__ */ t(q, { primary: `${i.expense_type} · ${P(i.amount, n.currency)}`, secondary: [g(i.expense_date), i.description ?? ""].filter(Boolean).join(" · ") }, u)) }) }),
        n.receipts.length > 0 && /* @__PURE__ */ t(O, { title: e("Receipts"), children: /* @__PURE__ */ t(W, { divided: !0, children: n.receipts.map((i) => /* @__PURE__ */ t(q, { primary: i.file_name, href: i.file_url }, i.name)) }) })
      ] })
    }
  );
}
function qa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.advanceList);
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Advances"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.advanceNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("Request an Advance")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Ft, {}), title: e("No advances"), description: e("Money paid to you ahead of work shows here, with what is left to settle.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        q,
        {
          primary: i.purpose,
          secondary: i.to_settle > 0 ? e("{0} · {1} left to settle", [P(i.advance_amount, i.currency), P(i.to_settle, i.currency)]) : P(i.advance_amount, i.currency),
          action: /* @__PURE__ */ t($, { value: i.docstatus === 0 ? "Draft" : i.status }),
          onClick: () => a(l.advanceRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
function Ma() {
  const a = N(), r = B(), n = M(v.requestAdvance), o = ue(() => ae.object({ purpose: ne(() => e("Purpose")), amount: wt(() => e("Amount"), { min: 1 }) }), []), s = he({ schema: o, defaultValues: { purpose: "", amount: null } });
  return /* @__PURE__ */ t(re, { title: e("Request an Advance"), onBack: () => a(l.advances), children: /* @__PURE__ */ m(
    me,
    {
      form: s,
      onSubmit: async (c) => {
        const i = await n.run({ purpose: c.purpose, amount: c.amount });
        r.success(e("Advance requested.")), a(l.advanceRecord(i));
      },
      children: [
        /* @__PURE__ */ t(H, { name: "purpose", label: e("Purpose"), required: !0, multiline: !0, rows: 2, hint: e("What the money is for, e.g. a field visit.") }),
        /* @__PURE__ */ t(Me, { name: "amount", label: e("Amount"), required: !0, min: 1, step: 1 }),
        /* @__PURE__ */ t(pe, { submitLabel: e("Request"), onCancel: () => a(l.advances) })
      ]
    }
  ) });
}
function Ta() {
  const a = N(), r = se(X().name), { data: n, isLoading: o, error: s, mutate: c } = x(v.advanceRecord, { name: r });
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
        V,
        {
          items: [
            { label: e("Amount"), value: P(n.advance_amount, n.currency) },
            { label: e("Paid"), value: P(n.paid_amount, n.currency) },
            { label: e("Claimed"), value: P(n.claimed_amount, n.currency) },
            { label: e("Returned"), value: P(n.return_amount, n.currency) },
            { label: e("Left to Settle"), value: P(n.to_settle, n.currency) },
            { label: e("Requested On"), value: g(n.posting_date) }
          ]
        }
      )
    }
  );
}
function $a() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.payslips), i = rt(o, s);
  return /* @__PURE__ */ t(ie, { title: e("Payslips"), onBack: () => a(""), loading: n, error: i.error, onRetry: s, children: i.needed ? /* @__PURE__ */ t(Ee, { what: e("Your payslips show once you confirm it is you."), busy: i.busy, onConfirm: i.confirm }) : c && !r?.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Qt, {}), title: e("No payslips yet"), description: e("Your payslips show here once payroll is run.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r ?? []).map((u) => /* @__PURE__ */ t(
    q,
    {
      primary: e("{0} to {1}", [g(u.start_date), g(u.end_date)]),
      secondary: e("Net pay {0}", [P(u.net_pay, u.currency)]),
      onClick: () => a(l.payRecord(u.name))
    },
    u.name
  )) }) });
}
function Ea() {
  const a = N(), r = se(X().name), { data: n, isLoading: o, error: s, mutate: c } = x(v.payslipRecord, { name: r }), i = rt(s, c), u = ce(), y = B(), p = M(v.confirmScreen), f = async () => {
    try {
      await ot(() => p.run({ screen: "payslips" }), u.verify);
    } catch (_) {
      _ instanceof at || y.error(e("The payslip could not be opened. Try again."));
      return;
    }
    const h = zn(r), d = window.open(h, "_blank");
    d ? d.opener = null : window.location.assign(h);
  };
  return /* @__PURE__ */ m(
    Q,
    {
      title: n ? e("{0} to {1}", [g(n.start_date), g(n.end_date)]) : e("Payslip"),
      subtitle: n?.employee_name,
      onBack: () => a(l.pay),
      actions: n ? /* @__PURE__ */ m(w, { loading: p.loading, onClick: f, children: [
        /* @__PURE__ */ t(Fn, {}),
        e("Open Payslip")
      ] }) : void 0,
      loading: o,
      error: i.error,
      onRetry: c,
      children: [
        i.needed && /* @__PURE__ */ t(Ee, { what: e("This payslip shows once you confirm it is you."), busy: i.busy, onConfirm: i.confirm }),
        n && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
          /* @__PURE__ */ t(
            V,
            {
              items: [
                { label: e("Gross Pay"), value: P(n.gross_pay, n.currency) },
                { label: e("Total Deduction"), value: P(n.total_deduction, n.currency) },
                { label: e("Net Pay"), value: P(n.net_pay, n.currency) }
              ]
            }
          ),
          /* @__PURE__ */ t(O, { title: e("Earnings"), children: /* @__PURE__ */ t(W, { divided: !0, children: n.earnings.map((h) => /* @__PURE__ */ t(q, { primary: h.component, action: P(h.amount, n.currency) }, h.component)) }) }),
          /* @__PURE__ */ t(O, { title: e("Deductions"), children: /* @__PURE__ */ t(W, { divided: !0, children: n.deductions.map((h) => /* @__PURE__ */ t(q, { primary: h.component, action: P(h.amount, n.currency) }, h.component)) }) })
        ] })
      ]
    }
  );
}
function Fa() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.timesheets);
  return /* @__PURE__ */ m(
    ie,
    {
      title: e("Timesheets"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: r?.weekly ? /* @__PURE__ */ m(w, { onClick: () => a(l.week(tt(U()))), children: [
        /* @__PURE__ */ t(Ge, {}),
        e("This Week")
      ] }) : void 0,
      children: [
        r && !r.weekly && /* @__PURE__ */ t(D, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer; they show here.") }),
        c && !r?.timesheets.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Ge, {}), title: e("No timesheets yet"), description: e("Your timesheets show here, newest first.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r?.timesheets ?? []).map((i) => /* @__PURE__ */ t(
          q,
          {
            primary: e("{0} to {1}", [g(i.start_date), g(i.end_date)]),
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
function mt(a) {
  return a === "Rest day" ? e("Rest Day") : a === "Public holiday" ? e("Public Holiday") : null;
}
function pt(a) {
  const r = ((/* @__PURE__ */ new Date(`${a}T12:00:00Z`)).getUTCDay() + 6) % 7;
  return [e("Monday"), e("Tuesday"), e("Wednesday"), e("Thursday"), e("Friday"), e("Saturday"), e("Sunday")][r];
}
function Pa() {
  const a = N(), r = B(), n = tt(X().week || U()), { data: o, isLoading: s, error: c, mutate: i } = x(v.timesheetWeek, { week_start: n }), u = M(v.saveTimesheetWeek), y = M(v.timesheetClaim), [p, f] = T([]), [h, d] = T(() => {
    const R = U();
    return R >= n && R <= we(n, 6) ? Xe(n).indexOf(R) : 0;
  }), [_, A] = T(!1), E = Ce(!1), L = (R) => {
    E.current = R, A(R);
  }, S = Te(ce().user, "timesheet-week", n), [I, J] = T(null), z = (R) => R.timesheet?.entries.length ? R.timesheet.entries : [ut([], R.default_activity_type)], ee = Ce(null);
  _e(() => {
    if (!o || o.week_start !== n) return;
    const R = ee.current === n;
    if (ee.current = n, R && E.current) return;
    const te = o.weekly && (!o.timesheet || o.timesheet.can_edit), Y = S.key ? Ze(S.key) : null;
    if (Y && te && Array.isArray(Y.value) && Y.value.length) {
      f(Y.value), L(!0), J(Y.saved);
      return;
    }
    Y && S.key && nn(S.key), f(z(o)), L(!1), J(null);
  }, [o, n]);
  const j = Xe(n), b = o?.days[h], C = !!o?.weekly && (!o.timesheet || o.timesheet.can_edit), Fe = ue(() => (o?.activity_types ?? []).map((R) => ({ value: R, label: R })), [o]), ve = (R) => {
    f(R), L(!0), S.keep(R);
  }, rn = () => {
    S.clear(), J(null), o && f(z(o)), L(!1);
  }, it = async (R) => {
    try {
      const te = await u.run({ week_start: n, entries: JSON.stringify(Zn(p)), send: R ? 1 : 0 });
      return r.success(R ? e("Week sent for approval.") : e("Week saved.")), S.clear(), J(null), L(!1), await i(), te;
    } catch {
      return null;
    }
  }, sn = o?.timesheet?.can_claim ? /* @__PURE__ */ t(
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
    /* @__PURE__ */ t(w, { variant: "outline", loading: u.loading, disabled: !_, onClick: () => it(!1), children: e("Save") }),
    o?.approval && /* @__PURE__ */ t(w, { loading: u.loading, onClick: () => it(!0), children: e("Send for Approval") })
  ] }) : void 0;
  return /* @__PURE__ */ t(
    re,
    {
      title: e("Week of {0}", [g(n)]),
      subtitle: e("{0} hours this week", [String(Gn(p))]),
      meta: o?.timesheet && /* @__PURE__ */ t($, { value: o.timesheet.docstatus === 1 ? "Approved" : o.timesheet.state }),
      onBack: () => a(l.timesheet),
      actions: sn,
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-4", children: [
        (u.errorMessage || y.errorMessage) && /* @__PURE__ */ t(D, { tone: "error", children: u.errorMessage || y.errorMessage }),
        I !== null && /* @__PURE__ */ t(
          D,
          {
            tone: "info",
            title: e("Restored From This Phone"),
            action: /* @__PURE__ */ t(w, { onClick: rn, children: e("Discard") }),
            children: e("What you entered on {0} was not saved yet. Save or send it when you are ready.", [g($e(I))])
          }
        ),
        !o.weekly && /* @__PURE__ */ t(D, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer.") }),
        C && o.approval && /* @__PURE__ */ t(D, { tone: o.approver_name ? "info" : "warning", children: fe(o.approver_name) }),
        o.timesheet?.state === "Returned" && o.timesheet.return_reason && /* @__PURE__ */ t(D, { tone: "warning", title: e("Returned to You"), children: o.timesheet.return_reason }),
        /* @__PURE__ */ m("div", { className: "flex items-center justify-between gap-2", children: [
          /* @__PURE__ */ t(He, { label: e("Previous Day"), variant: "outline", onClick: () => h > 0 ? d(h - 1) : a(l.week(we(n, -7))), children: /* @__PURE__ */ t($n, {}) }),
          /* @__PURE__ */ m("div", { className: "flex flex-col items-center", children: [
            /* @__PURE__ */ t(K, { size: "lg", children: pt(j[h]) }),
            /* @__PURE__ */ t(K, { size: "sm", muted: !0, children: g(j[h]) })
          ] }),
          /* @__PURE__ */ t(He, { label: e("Next Day"), variant: "outline", onClick: () => h < 6 ? d(h + 1) : a(l.week(we(n, 7))), children: /* @__PURE__ */ t(St, {}) })
        ] }),
        /* @__PURE__ */ m("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ t(be, { children: e("{0} hours entered", [String(tn(p, h))]) }),
          b?.attendance_hours !== null && b?.attendance_hours !== void 0 && /* @__PURE__ */ t(be, { variant: "outline", children: e("Attendance {0} hours", [String(b.attendance_hours)]) }),
          b && mt(b.kind) && /* @__PURE__ */ t(be, { tone: "info", children: mt(b.kind) }),
          b?.leave && /* @__PURE__ */ t(be, { tone: "warning", children: b.leave_fraction === 0.5 ? e("Half Day of Leave") : e("On Leave") })
        ] }),
        p.map((R) => /* @__PURE__ */ t(wn, { children: /* @__PURE__ */ m(bn, { className: "flex flex-col gap-3", children: [
          /* @__PURE__ */ m("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(Ne, { htmlFor: `activity-${R.row}`, children: e("Activity Type") }),
            /* @__PURE__ */ t(
              Cn,
              {
                id: `activity-${R.row}`,
                value: R.activity_type,
                options: Fe,
                disabled: !C,
                onValueChange: (te) => ve(p.map((Y) => Y.row === R.row ? { ...Y, activity_type: te } : Y))
              }
            )
          ] }),
          /* @__PURE__ */ m("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(Ne, { htmlFor: `description-${R.row}`, children: e("Description") }),
            /* @__PURE__ */ t(
              Ve,
              {
                id: `description-${R.row}`,
                value: R.description ?? "",
                disabled: !C,
                onChange: (te) => ve(p.map((Y) => Y.row === R.row ? { ...Y, description: te.target.value } : Y))
              }
            )
          ] }),
          /* @__PURE__ */ m("div", { className: "flex items-end gap-2", children: [
            /* @__PURE__ */ m("div", { className: "flex flex-1 flex-col gap-1", children: [
              /* @__PURE__ */ t(Ne, { htmlFor: `hours-${R.row}`, children: e("Hours on {0}", [pt(j[h])]) }),
              /* @__PURE__ */ t(
                Ve,
                {
                  id: `hours-${R.row}`,
                  type: "number",
                  inputMode: "decimal",
                  min: 0,
                  max: 24,
                  step: 0.25,
                  value: R.hours[h] ? String(R.hours[h]) : "",
                  disabled: !C,
                  onChange: (te) => ve(Xn(p, R.row, h, te.target.value))
                }
              )
            ] }),
            C && p.length > 1 && /* @__PURE__ */ t(He, { label: e("Remove Line"), variant: "ghost", onClick: () => ve(p.filter((te) => te.row !== R.row)), children: /* @__PURE__ */ t(In, {}) })
          ] })
        ] }) }, R.row)),
        C && /* @__PURE__ */ m("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ m(w, { variant: "outline", onClick: () => ve([...p, ut(p, o.default_activity_type)]), children: [
            /* @__PURE__ */ t(ye, {}),
            e("Add Line")
          ] }),
          o.previous_entries.length > 0 && /* @__PURE__ */ m(w, { variant: "outline", onClick: () => ve(Kn(o.previous_entries)), children: [
            /* @__PURE__ */ t(En, {}),
            e("Copy Last Week")
          ] })
        ] }),
        o.checks.length > 0 && /* @__PURE__ */ t(O, { title: e("Weekly Check"), children: /* @__PURE__ */ t(W, { divided: !0, children: o.checks.map((R) => /* @__PURE__ */ t(q, { primary: R }, R)) }) })
      ] })
    }
  );
}
function Ba() {
  const a = N(), r = se(X().name), { data: n, isLoading: o, error: s, mutate: c } = x(v.timesheetRecord, { name: r });
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
          V,
          {
            items: [
              { label: e("From"), value: g(n.start_date) },
              { label: e("To"), value: g(n.end_date) },
              { label: e("Total Hours"), value: String(n.total_hours ?? 0) }
            ]
          }
        ),
        /* @__PURE__ */ t(W, { divided: !0, children: n.lines.map((i, u) => /* @__PURE__ */ t(q, { primary: e("{0} · {1} hours", [g(i.date), String(i.hours)]), secondary: [i.activity_type, i.description].filter(Boolean).join(" · ") }, u)) })
      ] })
    }
  );
}
function Ha() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.toilList);
  return /* @__PURE__ */ m(
    ie,
    {
      title: e("Time Off in Lieu"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: r?.eligible ? /* @__PURE__ */ m(w, { onClick: () => a(l.toilNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("Claim Time Off")
      ] }) : void 0,
      children: [
        r && !r.eligible && /* @__PURE__ */ t(D, { tone: "info", children: e("Your grade does not bank extra hours as time off. Ask HR if you think it should.") }),
        r?.eligible && /* @__PURE__ */ m(Ct, { columns: 2, children: [
          /* @__PURE__ */ t(Ye, { label: e("Days Left"), value: String(r.left) }),
          /* @__PURE__ */ t(
            Ye,
            {
              label: e("Lapsing in 30 Days"),
              value: String(r.lapsing),
              hint: r.first_lapse ? e("First on {0}", [g(r.first_lapse)]) : void 0
            }
          )
        ] }),
        c && !r?.claims.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(Se, {}), title: e("No claims yet"), description: e("Claim the extra hours you worked, a day at a time.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r?.claims ?? []).map((i) => /* @__PURE__ */ t(
          q,
          {
            primary: e("{0} hours · {1} days", [String(i.total_hours ?? 0), String(i.days ?? 0)]),
            secondary: i.status === "Approved" && i.lapses_on ? e("{0} days left, usable until {1}", [String(i.days_left ?? 0), g(i.lapses_on)]) : g(i.creation),
            action: /* @__PURE__ */ t($, { value: i.status }),
            onClick: () => a(l.toilRecord(i.name))
          },
          i.name
        )) })
      ]
    }
  );
}
const yt = () => ({ work_date: "", hours: null, work_done: "" });
function Oa() {
  const a = N(), r = B(), [n] = vt(), o = n.get("claim"), s = x(v.toilList), c = x(v.toilRecord, { name: o ?? "" }, { enabled: !!o }), i = M(v.saveToilClaim), u = mn(), [y, p] = T(!1), [f, h] = T(null), d = he({ defaultValues: { lines: [yt()], note: "" } });
  _e(() => {
    c.data && d.reset({ lines: c.data.lines.map((L) => ({ work_date: L.work_date, hours: L.hours, work_done: L.work_done })), note: c.data.note ?? "" });
  }, [c.data, d]);
  const _ = async () => {
    if (s.data) {
      p(!0), h(null);
      try {
        const L = s.data.from_attendance ? "Attendance" : "Timesheet", S = U(), I = await u.get(v.extraTime, { employee: s.data.employee, from_date: we(S, -30), to_date: S, source: L }) ?? [], J = d.getValues("lines").filter((z) => z.work_date);
        d.setValue("lines", ia(J, I), { shouldDirty: !0 }), h(I.length ? e("{0} days found in the last 30 days. Say what the work was on each.", [String(I.length)]) : e("The records show no extra hours you have not claimed in the last 30 days."));
      } catch {
        h(e("The records could not be read. Enter the days yourself."));
      } finally {
        p(!1);
      }
    }
  }, A = async (L) => {
    const S = await i.run({ lines: JSON.stringify(L.lines.filter((I) => I.work_date)), note: L.note, name: o ?? void 0 });
    r.success(e("Claim saved. Send it when it is ready.")), a(l.toilRecord(S));
  }, E = s.data && (s.data.from_attendance || s.data.from_timesheets);
  return /* @__PURE__ */ m(
    re,
    {
      title: o ? e("Change Claim") : e("Claim Time Off"),
      onBack: () => a(o ? l.toilRecord(o) : l.toil),
      loading: s.isLoading || c.isLoading,
      error: s.error ?? c.error,
      actions: E ? /* @__PURE__ */ t(w, { variant: "outline", loading: y, onClick: _, children: e("Fill from Records") }) : void 0,
      children: [
        s.data && /* @__PURE__ */ t(D, { tone: s.data.approver_name ? "info" : "warning", children: fe(s.data.approver_name) }),
        f && /* @__PURE__ */ t(D, { tone: "info", children: f }),
        /* @__PURE__ */ m(me, { form: d, onSubmit: A, children: [
          /* @__PURE__ */ t(
            Le,
            {
              name: "lines",
              label: e("Days Worked"),
              minRows: 1,
              addLabel: e("Add a Day"),
              newRow: yt,
              renderRow: (L) => /* @__PURE__ */ m(de, { children: [
                /* @__PURE__ */ t(oe, { name: L("work_date"), label: e("Date"), required: !0, maxDate: U() }),
                /* @__PURE__ */ t(Me, { name: L("hours"), label: e("Hours Worked"), min: 0, max: 24, step: 0.25 }),
                /* @__PURE__ */ t(H, { name: L("work_done"), label: e("Work Done"), required: !0, multiline: !0, rows: 2 })
              ] })
            }
          ),
          /* @__PURE__ */ t(H, { name: "note", label: e("Note"), multiline: !0, rows: 2, hint: e("Anything your approver should know about these days.") }),
          /* @__PURE__ */ t(pe, { submitLabel: e("Save Claim"), onCancel: () => a(o ? l.toilRecord(o) : l.toil) })
        ] })
      ]
    }
  );
}
function Ia() {
  const a = N(), r = B(), n = se(X().name), { data: o, isLoading: s, error: c, mutate: i } = x(v.toilRecord, { name: n }), u = M(v.toilAction), y = async (f) => {
    try {
      await u.run({ name: n, action: f }), r.success(e("Claim sent.")), await i();
    } catch {
    }
  }, p = o && /* @__PURE__ */ m("div", { className: "flex gap-2", children: [
    o.can_edit && /* @__PURE__ */ t(w, { variant: "outline", onClick: () => a(`${l.toilNew}?claim=${encodeURIComponent(n)}`), children: e("Change") }),
    o.actions.map((f) => /* @__PURE__ */ t(w, { loading: u.loading, onClick: () => y(f), children: f === "Send for Authorisation" ? e("Send for Authorisation") : e("Send for Approval") }, f)),
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
        u.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: u.errorMessage }),
        o.stage.items.length > 0 && /* @__PURE__ */ t(D, { tone: o.stage.tone, children: /* @__PURE__ */ t("div", { className: "flex flex-col gap-1", children: o.stage.items.map((f) => /* @__PURE__ */ m(K, { children: [
          /* @__PURE__ */ m("strong", { children: [
            f.label,
            ":"
          ] }),
          " ",
          f.text
        ] }, f.label)) }) }),
        /* @__PURE__ */ t(
          V,
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
        /* @__PURE__ */ t(O, { title: e("Days Worked"), children: /* @__PURE__ */ t(W, { divided: !0, children: o.lines.map((f) => /* @__PURE__ */ t(
          q,
          {
            primary: e("{0} · {1} hours", [g(f.work_date), String(f.hours ?? f.planned_hours ?? 0)]),
            secondary: [f.work_done, f.supported_by ?? ""].filter(Boolean).join(" · ")
          },
          f.work_date
        )) }) })
      ] })
    }
  );
}
function an(a) {
  return a.travel_from && a.travel_to ? e("{0} to {1}", [a.travel_from, a.travel_to]) : a.travel_to || a.travel_from || a.purpose_of_travel;
}
function za() {
  const a = N(), { data: r, isLoading: n, error: o, mutate: s, hasLoaded: c } = x(v.travelList);
  return /* @__PURE__ */ t(
    ie,
    {
      title: e("Travel Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: s,
      actions: /* @__PURE__ */ m(w, { onClick: () => a(l.travelNew), children: [
        /* @__PURE__ */ t(ye, {}),
        e("New Travel Request")
      ] }),
      children: c && !r?.length ? /* @__PURE__ */ t(Z, { icon: /* @__PURE__ */ t(jt, {}), title: e("No travel requests yet"), description: e("Ask to travel for work. Your line manager approves it.") }) : /* @__PURE__ */ t(W, { divided: !0, children: (r ?? []).map((i) => /* @__PURE__ */ t(
        q,
        {
          primary: an(i),
          secondary: [i.purpose_of_travel, i.departure_date ? g(i.departure_date) : g(i.creation)].filter(Boolean).join(" · "),
          action: /* @__PURE__ */ t($, { value: i.state }),
          onClick: () => a(l.travelRecord(i.name))
        },
        i.name
      )) })
    }
  );
}
const on = () => ({ travel_from: "", travel_to: "", mode_of_travel: "", departure_date: "", arrival_date: "", lodging_required: !1 }), ja = () => ({ expense_type: "", total_amount: null, comments: "" }), ze = () => ({ travel_type: "", purpose_of_travel: "", travel_funding: "", description: "", itinerary: [on()], costings: [] });
function De(a) {
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
function Ya() {
  const a = N(), r = B(), n = x(v.travelOptions), o = M(v.requestTravel), s = ue(
    () => ae.object({
      travel_type: ne(() => e("Travel Type")),
      purpose_of_travel: ne(() => e("Purpose of Travel")),
      itinerary: ae.array(ae.object({ travel_from: ne(() => e("From")), travel_to: ne(() => e("To")) }).loose()).min(1)
    }).loose(),
    []
  ), c = he({ schema: s, defaultValues: ze() }), i = Te(ce().user, "travel-request", "new"), [u, y] = T(null);
  _e(() => {
    i.restored && Array.isArray(i.restored.value?.itinerary) && (c.reset({ ...ze(), ...i.restored.value }), y(i.restored.saved), i.dismiss());
    const d = c.watch((_) => i.keep(_));
    return () => d.unsubscribe();
  }, []);
  const p = () => {
    i.clear(), y(null), c.reset(ze());
  }, f = async (d) => {
    const _ = ca(d.itinerary, d.costings), A = await o.run({
      travel_type: d.travel_type,
      purpose_of_travel: d.purpose_of_travel,
      travel_funding: d.travel_funding || void 0,
      description: d.description,
      itinerary: JSON.stringify(_.itinerary),
      costings: JSON.stringify(_.costings),
      send: 1
    });
    i.clear(), r.success(n.data?.approver_name ? e("Travel request sent to {0}.", [n.data.approver_name]) : e("Travel request sent.")), a(l.travelRecord(A.name));
  }, h = (d) => (d ?? []).map((_) => ({ value: _, label: De(_) }));
  return /* @__PURE__ */ m(re, { title: e("New Travel Request"), onBack: () => a(l.travel), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    u !== null && /* @__PURE__ */ t(D, { tone: "info", title: e("Restored From This Phone"), action: /* @__PURE__ */ t(w, { onClick: p, children: e("Start Again") }), children: e("You started this request on {0} and had not sent it.", [g($e(u))]) }),
    n.data && /* @__PURE__ */ t(D, { tone: n.data.approver_name ? "info" : "warning", children: fe(n.data.approver_name) }),
    /* @__PURE__ */ m(me, { form: c, onSubmit: f, children: [
      /* @__PURE__ */ t(le, { name: "travel_type", label: e("Travel Type"), required: !0, options: h(n.data?.travel_types) }),
      /* @__PURE__ */ t(le, { name: "purpose_of_travel", label: e("Purpose of Travel"), required: !0, options: (n.data?.purposes ?? []).map((d) => ({ value: d, label: d })), hint: n.data && !n.data.purposes.length ? e("HR has not set up purposes of travel yet. Ask them to.") : void 0 }),
      /* @__PURE__ */ t(le, { name: "travel_funding", label: e("Travel Funding"), options: h(n.data?.funding) }),
      /* @__PURE__ */ t(
        Le,
        {
          name: "itinerary",
          label: e("Journeys"),
          minRows: 1,
          addLabel: e("Add a Journey"),
          newRow: on,
          renderRow: (d) => /* @__PURE__ */ m(de, { children: [
            /* @__PURE__ */ t(H, { name: d("travel_from"), label: e("From"), required: !0 }),
            /* @__PURE__ */ t(H, { name: d("travel_to"), label: e("To"), required: !0 }),
            /* @__PURE__ */ t(le, { name: d("mode_of_travel"), label: e("Mode of Travel"), options: h(n.data?.modes) }),
            /* @__PURE__ */ t(ct, { name: d("departure_date"), label: e("Departure") }),
            /* @__PURE__ */ t(ct, { name: d("arrival_date"), label: e("Arrival") }),
            /* @__PURE__ */ t(qe, { name: d("lodging_required"), label: e("Lodging Required") })
          ] })
        }
      ),
      /* @__PURE__ */ t(
        Le,
        {
          name: "costings",
          label: e("Expected Costs"),
          addLabel: e("Add a Cost"),
          newRow: ja,
          emptyText: e("None yet. Add what the trip is expected to cost, if you know."),
          renderRow: (d) => /* @__PURE__ */ m(de, { children: [
            /* @__PURE__ */ t(le, { name: d("expense_type"), label: e("Expense Type"), options: (n.data?.expense_types ?? []).map((_) => ({ value: _, label: _ })) }),
            /* @__PURE__ */ t(Me, { name: d("total_amount"), label: e("Amount ({0})", [n.data?.currency ?? ""]), min: 0, step: 0.01 }),
            /* @__PURE__ */ t(H, { name: d("comments"), label: e("Comments") })
          ] })
        }
      ),
      /* @__PURE__ */ t(H, { name: "description", label: e("Other Details"), multiline: !0, rows: 3 }),
      /* @__PURE__ */ t(pe, { submitLabel: e("Send for Approval"), onCancel: () => a(l.travel) })
    ] })
  ] });
}
function Va() {
  const a = N(), r = B(), n = se(X().name), { data: o, isLoading: s, error: c, mutate: i } = x(v.travelRecord, { name: n }), u = M(v.travelAction), y = async () => {
    try {
      await u.run({ name: n, action: "Send for Approval" }), r.success(e("Travel request sent.")), await i();
    } catch {
    }
  };
  return /* @__PURE__ */ t(
    Q,
    {
      title: o ? an({ ...o.itinerary[0] ?? { travel_from: null, travel_to: null }, purpose_of_travel: o.purpose_of_travel }) : e("Travel Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t($, { value: o.state }),
      onBack: () => a(l.travel),
      actions: o?.can_send ? /* @__PURE__ */ t(w, { loading: u.loading, onClick: y, children: e("Send for Approval") }) : void 0,
      loading: s,
      error: c,
      onRetry: i,
      children: o && /* @__PURE__ */ m("div", { className: "flex flex-col gap-6", children: [
        u.errorMessage && /* @__PURE__ */ t(D, { tone: "error", children: u.errorMessage }),
        o.mine && o.state === "Pending Approval" && /* @__PURE__ */ t(D, { tone: "info", children: fe(o.approver_name) }),
        /* @__PURE__ */ t(
          V,
          {
            items: [
              { label: e("Purpose of Travel"), value: o.purpose_of_travel },
              { label: e("Travel Type"), value: De(o.travel_type) },
              { label: e("Travel Funding"), value: o.travel_funding ? De(o.travel_funding) : null, hideWhenEmpty: !0 },
              { label: e("Line Manager"), value: o.approver_name, hideWhenEmpty: !0 },
              { label: e("Other Details"), value: o.description, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(O, { title: e("Journeys"), children: /* @__PURE__ */ t(W, { divided: !0, children: o.itinerary.map((p, f) => /* @__PURE__ */ t(
          q,
          {
            primary: e("{0} to {1}", [p.travel_from || "?", p.travel_to || "?"]),
            secondary: [p.mode_of_travel ? De(p.mode_of_travel) : "", p.departure_date ? Re(p.departure_date) : "", p.lodging_required ? e("Lodging required") : ""].filter(Boolean).join(" · ")
          },
          f
        )) }) }),
        o.costings.length > 0 && /* @__PURE__ */ t(O, { title: e("Expected Costs"), children: /* @__PURE__ */ t(W, { divided: !0, children: o.costings.map((p, f) => /* @__PURE__ */ t(q, { primary: p.expense_type || e("Other"), secondary: p.comments ?? void 0, action: o.currency ? P(p.total_amount, o.currency) : String(p.total_amount) }, f)) }) }),
        !o.mine && /* @__PURE__ */ t(K, { muted: !0, children: e("Decide this request from Approvals.") })
      ] })
    }
  );
}
const Ua = [
  { path: "leave", element: /* @__PURE__ */ t(ba, {}) },
  { path: "leave/new", element: /* @__PURE__ */ t(Ca, {}) },
  { path: "leave/:name", element: /* @__PURE__ */ t(Ra, {}) },
  { path: "cover", element: /* @__PURE__ */ t(pa, {}) },
  { path: "cover/:name", element: /* @__PURE__ */ t(ya, {}) },
  { path: "toil", element: /* @__PURE__ */ t(Ha, {}) },
  { path: "toil/new", element: /* @__PURE__ */ t(Oa, {}) },
  { path: "toil/:name", element: /* @__PURE__ */ t(Ia, {}) },
  { path: "timesheet", element: /* @__PURE__ */ t(Fa, {}) },
  { path: "timesheet/week/:week", element: /* @__PURE__ */ t(Pa, {}) },
  { path: "timesheet/:name", element: /* @__PURE__ */ t(Ba, {}) },
  { path: "expenses", element: /* @__PURE__ */ t(La, {}) },
  { path: "expenses/new", element: /* @__PURE__ */ t(Sa, {}) },
  { path: "expenses/:name", element: /* @__PURE__ */ t(Wa, {}) },
  { path: "advances", element: /* @__PURE__ */ t(qa, {}) },
  { path: "advances/new", element: /* @__PURE__ */ t(Ma, {}) },
  { path: "advances/:name", element: /* @__PURE__ */ t(Ta, {}) },
  { path: "pay", element: /* @__PURE__ */ t($a, {}) },
  { path: "pay/:name", element: /* @__PURE__ */ t(Ea, {}) },
  { path: "check-in", element: /* @__PURE__ */ t(ea, {}) },
  { path: "attendance", element: /* @__PURE__ */ t(ta, {}) },
  { path: "attendance/new", element: /* @__PURE__ */ t(na, {}) },
  { path: "attendance/:name", element: /* @__PURE__ */ t(ht, { doctype: "Attendance Request" }) },
  { path: "shifts", element: /* @__PURE__ */ t(aa, {}) },
  { path: "shifts/new", element: /* @__PURE__ */ t(oa, {}) },
  { path: "shifts/:name", element: /* @__PURE__ */ t(ht, { doctype: "Shift Request" }) },
  { path: "me", element: /* @__PURE__ */ t(Aa, {}) },
  { path: "me/payout/new", element: /* @__PURE__ */ t(Na, {}) },
  { path: "me/payout/:name", element: /* @__PURE__ */ t(Da, {}) },
  { path: "travel", element: /* @__PURE__ */ t(za, {}) },
  { path: "travel/new", element: /* @__PURE__ */ t(Ya, {}) },
  { path: "travel/:name", element: /* @__PURE__ */ t(Va, {}) },
  { path: "compensatory-leave", element: /* @__PURE__ */ t(ua, {}) },
  { path: "compensatory-leave/new", element: /* @__PURE__ */ t(ha, {}) },
  { path: "compensatory-leave/:name", element: /* @__PURE__ */ t(ma, {}) }
], no = dn({
  key: "seal_hrms.my_hr",
  home: fa,
  routes: Ua,
  records: Rt,
  settings: [{ key: "hr_notifications", label: "HR", kind: "push-category" }]
});
export {
  Ua as ROUTES,
  no as default
};
