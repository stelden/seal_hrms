var Et = Object.defineProperty;
var Tt = (a, i, n) => i in a ? Et(a, i, { enumerable: !0, configurable: !0, writable: !0, value: n }) : a[i] = n;
var Be = (a, i, n) => Tt(a, typeof i != "symbol" ? i + "" : i, n);
import { jsx as t, jsxs as h, Fragment as de } from "react/jsx-runtime";
import { useShell as $e, defineSection as Ht } from "@stelden/seal-frontend/section";
import { useContext as Bt, createContext as Pt, forwardRef as Ye, createElement as Re, useCallback as Ot, useState as T, useMemo as oe, useEffect as Ve } from "react";
import { useParams as U, useSearchParams as Ue } from "react-router";
import { useGet as N, usePost as S, formatDateTime as ve, formatDate as _, uploadFile as Je, formatCurrency as $, useFrappeCall as Ft } from "@stelden/seal-frontend";
import { z as ae, required as ye, frappeDate as me, useSealForm as ie, SealForm as re, RadioInput as Ge, DateInput as te, CheckboxInput as Ke, TextInput as z, FormActions as ue, SelectInput as ge, Wizard as It, AutocompleteInput as _e, FileInput as Ze, MobileInputKE as zt, amount as Qe, RowsInput as Xe, NumberInput as Ee } from "@stelden/seal-frontend/forms";
import { toneMap as jt, StatusChip as Yt, __ as e, useNotify as F, FormPage as K, Alert as E, Button as b, Text as G, Section as B, List as D, ListItem as L, ListPage as Z, EmptyState as Q, DetailPage as J, DescriptionList as j, TabsNav as Vt, TabPanel as ke, SealDialog as et, Textarea as Ut, ConfirmDialog as tt, DashboardPage as Jt, StatGrid as nt, StatCard as xe, Badge as he, FilterChips as Gt, Label as fe, Input as Ne, IconButton as we, Card as Kt, CardContent as Zt, Select as Qt } from "@stelden/seal-frontend/ui";
const V = (a) => encodeURIComponent(a);
function X(a) {
  if (!a) return "";
  try {
    return decodeURIComponent(a);
  } catch {
    return a;
  }
}
const s = {
  leave: "leave",
  leaveNew: "leave/new",
  leaveRecord: (a) => `leave/${V(a)}`,
  cover: "cover",
  handover: (a) => `cover/${V(a)}`,
  toil: "toil",
  toilNew: "toil/new",
  toilRecord: (a) => `toil/${V(a)}`,
  timesheet: "timesheet",
  week: (a) => `timesheet/week/${a}`,
  timesheetRecord: (a) => `timesheet/${V(a)}`,
  expenses: "expenses",
  expenseNew: "expenses/new",
  expenseRecord: (a) => `expenses/${V(a)}`,
  advances: "advances",
  advanceNew: "advances/new",
  advanceRecord: (a) => `advances/${V(a)}`,
  pay: "pay",
  payRecord: (a) => `pay/${V(a)}`,
  checkIn: "check-in",
  attendance: "attendance",
  attendanceNew: "attendance/new",
  attendanceRecord: (a) => `attendance/${V(a)}`,
  shifts: "shifts",
  shiftNew: "shifts/new",
  shiftRecord: (a) => `shifts/${V(a)}`,
  me: "me",
  payoutNew: "me/payout/new",
  payoutRecord: (a) => `me/payout/${V(a)}`
}, at = {
  "Leave Application": { list: s.leave, record: s.leaveRecord, create: s.leaveNew },
  "Leave Allocation": { list: s.leave },
  "Task Assignment": { list: s.cover, record: s.handover },
  "Time Off in Lieu Claim": { list: s.toil, record: s.toilRecord, create: s.toilNew },
  Timesheet: { list: s.timesheet, record: s.timesheetRecord },
  "Expense Claim": { list: s.expenses, record: s.expenseRecord, create: s.expenseNew },
  "Employee Advance": { list: s.advances, record: s.advanceRecord, create: s.advanceNew },
  "Salary Slip": { list: s.pay, record: s.payRecord },
  Employee: { list: s.me, record: () => s.me },
  "Employee Checkin": { list: s.checkIn, record: () => s.checkIn, create: s.checkIn },
  "Attendance Request": { list: s.attendance, record: s.attendanceRecord, create: s.attendanceNew },
  "Shift Request": { list: s.shifts, record: s.shiftRecord, create: s.shiftNew },
  "Employee Dependent and Beneficiary": { list: s.me, record: () => s.me },
  "Payout Change Request": { list: s.me, record: s.payoutRecord, create: s.payoutNew }
};
function Xt(a) {
  return at[a]?.list;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const en = (a) => a?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function tn(a, i, n = []) {
  if (i == null)
    throw new Error("[lucide]: iconNode is required when icon name is used");
  return {
    name: en(a),
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
const nn = (a) => {
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
const an = (a) => {
  const i = nn(a);
  return i.charAt(0).toUpperCase() + i.slice(1);
};
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ae = (...a) => a.filter((i, n, o) => !!i && i.trim() !== "" && o.indexOf(i) === n).join(" ").trim();
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ne = {
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
function be(a) {
  return a != null;
}
function on(a, i = {}) {
  const n = i.attributeNames ?? {}, o = (p) => n[p] ?? p, l = a.size ?? a.width ?? ne.width, c = a.size ?? a.height ?? ne.height, r = a.aliases?.filter((p) => typeof p == "string" && p.trim() !== "").map((p) => `lucide-${p}`) ?? [], u = [...a.name ? [`lucide-${a.name}`] : [], ...r], y = i.className?.split(" ").filter(Boolean) ?? [], v = i.includeDefaultClasses === !1 ? Ae(...y) : Ae("lucide", ...u, ...y), m = i.absoluteStrokeWidth ? Number(i.strokeWidth ?? ne["stroke-width"]) * Number(a.size ?? a.width ?? ne.width) / Number(i.size ?? i.width ?? ne.width) : i.strokeWidth ?? ne["stroke-width"];
  return [
    "svg",
    {
      ...Object.entries(ne).reduce((p, [R, x]) => (p[o(R)] = x, p), {}),
      ..."color" in i && i.color && {
        [o("stroke")]: i.color
      },
      ..."size" in i && be(i.size) && {
        [o("width")]: i.size,
        [o("height")]: i.size
      },
      ..."width" in i && be(i.width) && {
        [o("width")]: i.width
      },
      ..."height" in i && be(i.height) && {
        [o("height")]: i.height
      },
      [o("stroke-width")]: m,
      ...v && {
        [o("class")]: v
      },
      [o("viewBox")]: `0 0 ${l} ${c}`,
      ...i.hasA11yProp === !1 ? {
        [o("aria-hidden")]: "true"
      } : {},
      ..."attributes" in i && i.attributes
    },
    a.node.map((p) => {
      const [R, x, H] = p, f = i.nonScalingStroke ? { [o("vector-effect")]: "non-scaling-stroke", ...x } : x;
      return H ? [R, f, H] : [R, f];
    })
  ];
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
function rn(a, i = {}) {
  return on(a, {
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
const sn = (a) => {
  for (const i in a)
    if (i.startsWith("aria-") || i === "role" || i === "title")
      return !0;
  return !1;
}, ln = Pt({}), cn = () => Bt(ln), dn = Ye(
  ({
    color: a,
    size: i,
    width: n,
    height: o,
    strokeWidth: l,
    absoluteStrokeWidth: c,
    nonScalingStroke: r,
    className: u = "",
    children: y,
    iconNode: v = [],
    icon: m = {
      node: v,
      aliases: [],
      size: 24
    },
    ...d
  }, p) => {
    const {
      size: R = 24,
      strokeWidth: x = 2,
      absoluteStrokeWidth: H = !1,
      nonScalingStroke: f = !1,
      color: q = "currentColor",
      className: I = ""
    } = cn() ?? {}, P = !!y || sn(d), [ee, le, w = []] = rn(m, {
      color: a ?? q,
      width: n ?? i ?? R,
      height: o ?? i ?? R,
      strokeWidth: l ?? x,
      absoluteStrokeWidth: c ?? H,
      nonScalingStroke: r ?? f,
      className: Ae(I, u),
      hasA11yProp: P,
      attributes: d
    });
    return Re(
      ee,
      {
        ref: p,
        ...le
      },
      [
        ...w.map(([O, C]) => Re(O, C)),
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
function W(a, i = [], n = []) {
  const o = typeof a == "string" ? tn(a, i, n) : a, l = Ye(
    ({ className: c, ...r }, u) => Re(dn, {
      ref: u,
      icon: o,
      className: c,
      ...r
    })
  );
  return o.name && (l.displayName = an(o.name)), l;
}
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ot = {
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
ot.node;
const De = W(ot);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const it = {
  name: "chevron-left",
  size: 24,
  node: [["path", { d: "m15 18-6-6 6-6", key: "1wnfg3" }]]
};
it.node;
const un = W(it);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const rt = {
  name: "chevron-right",
  size: 24,
  node: [["path", { d: "m9 18 6-6-6-6", key: "mthhwq" }]]
};
rt.node;
const st = W(rt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const lt = {
  name: "clock",
  size: 24,
  node: [
    ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
    ["path", { d: "M12 6v6l4 2", key: "mmk7yg" }]
  ]
};
lt.node;
const Le = W(lt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ct = {
  name: "copy",
  size: 24,
  node: [
    ["rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2", key: "17jyea" }],
    ["path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2", key: "zix9uf" }]
  ]
};
ct.node;
const hn = W(ct);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const dt = {
  name: "download",
  size: 24,
  node: [
    ["path", { d: "M12 15V3", key: "m9g1x1" }],
    ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
    ["path", { d: "m7 10 5 5 5-5", key: "brsn70" }]
  ]
};
dt.node;
const mn = W(dt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ut = {
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
ut.node;
const pn = W(ut);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ht = {
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
ht.node;
const Pe = W(ht);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const mt = {
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
mt.node;
const pt = W(mt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const yt = {
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
yt.node;
const Se = W(yt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ft = {
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
ft.node;
const yn = W(ft);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const vt = {
  name: "log-in",
  size: 24,
  node: [
    ["path", { d: "m10 17 5-5-5-5", key: "1bsop3" }],
    ["path", { d: "M15 12H3", key: "6jk70r" }],
    ["path", { d: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4", key: "u53s6r" }]
  ]
};
vt.node;
const fn = W(vt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const gt = {
  name: "log-out",
  size: 24,
  node: [
    ["path", { d: "m16 17 5-5-5-5", key: "1bji2h" }],
    ["path", { d: "M21 12H9", key: "dn1m92" }],
    ["path", { d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", key: "1uf3rs" }]
  ]
};
gt.node;
const vn = W(gt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const _t = {
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
_t.node;
const Te = W(_t);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const kt = {
  name: "plus",
  size: 24,
  node: [
    ["path", { d: "M5 12h14", key: "1ays0h" }],
    ["path", { d: "M12 5v14", key: "s699le" }]
  ]
};
kt.node;
const se = W(kt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const wt = {
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
wt.node;
const Me = W(wt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const bt = {
  name: "repeat",
  size: 24,
  node: [
    ["path", { d: "m17 2 4 4-4 4", key: "nntrym" }],
    ["path", { d: "M3 11v-1a4 4 0 0 1 4-4h14", key: "84bu3i" }],
    ["path", { d: "m7 22-4-4 4-4", key: "1wqhfi" }],
    ["path", { d: "M21 13v1a4 4 0 0 1-4 4H3", key: "1rx37r" }]
  ]
};
bt.node;
const Ct = W(bt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Rt = {
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
Rt.node;
const gn = W(Rt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const xt = {
  name: "users",
  size: 24,
  node: [
    ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
    ["path", { d: "M16 3.128a4 4 0 0 1 0 7.744", key: "16gr8j" }],
    ["path", { d: "M22 21v-2a4 4 0 0 0-3-3.87", key: "kshegd" }],
    ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }]
  ]
};
xt.node;
const Nt = W(xt);
/**
 * @license lucide-react v1.71.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const At = {
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
At.node;
const Dt = W(At), k = "seal_hrms.my_desk.api.", g = {
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
function _n(a) {
  return `/api/method/${g.payslipPdf}?name=${encodeURIComponent(a)}`;
}
function A() {
  const a = $e();
  return Ot((i) => a.navigate(i), [a]);
}
const kn = jt(
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
function wn(a) {
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
function M({ value: a }) {
  return a ? /* @__PURE__ */ t(Yt, { status: a, label: wn(a), toneOf: kn }) : null;
}
const bn = 864e5;
function Lt(a) {
  const [i, n, o] = a.split("-").map(Number);
  return Date.UTC(i, n - 1, o);
}
function Cn(a) {
  return new Date(a).toISOString().slice(0, 10);
}
function ce(a, i) {
  return Cn(Lt(a) + i * bn);
}
function He(a) {
  const i = (new Date(Lt(a)).getUTCDay() + 6) % 7;
  return ce(a, -i);
}
function Y(a = /* @__PURE__ */ new Date()) {
  const i = (n) => String(n).padStart(2, "0");
  return `${a.getFullYear()}-${i(a.getMonth() + 1)}-${i(a.getDate())}`;
}
function We(a) {
  return Array.from({ length: 7 }, (i, n) => ce(a, n));
}
function pe(a) {
  const i = typeof a == "number" ? a : Number.parseFloat(String(a ?? ""));
  return Number.isFinite(i) && i > 0 ? Math.round(i * 100) / 100 : 0;
}
function St(a, i) {
  return Math.round(a.reduce((n, o) => n + pe(o.hours[i]), 0) * 100) / 100;
}
function Rn(a) {
  return Math.round(We("2000-01-03").reduce((i, n, o) => i + St(a, o), 0) * 100) / 100;
}
function Oe(a, i) {
  return { row: a.reduce((o, l) => Math.max(o, l.row), 0) + 1, activity_type: i, description: "", is_billable: 0, hours: [0, 0, 0, 0, 0, 0, 0] };
}
function xn(a) {
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
function Nn(a, i, n, o) {
  return a.map((l) => l.row === i ? { ...l, hours: l.hours.map((c, r) => pe(r === n ? o : c)) } : l);
}
function An(a) {
  return a.filter((i) => i.hours.some((n) => pe(n) > 0) || (i.description ?? "").trim()).map((i, n) => ({ ...i, row: n + 1, hours: Array.from({ length: 7 }, (o, l) => pe(i.hours[l])) }));
}
function Dn() {
  return "geolocation" in navigator ? new Promise(
    (a) => navigator.geolocation.getCurrentPosition(
      (i) => a({ latitude: i.coords.latitude, longitude: i.coords.longitude }),
      () => a(null),
      { enableHighAccuracy: !0, timeout: 1e4, maximumAge: 6e4 }
    )
  ) : Promise.resolve(null);
}
function Ln() {
  const a = A(), i = F(), { data: n, isLoading: o, error: l, mutate: c } = N(g.checkinStatus), r = S(g.checkIn), [u, y] = T(!1), [v, m] = T(!1), d = async () => {
    if (!n) return;
    m(!1);
    let p = null;
    n.location && (y(!0), p = await Dn(), y(!1), m(!p));
    try {
      await r.run({ log_type: n.next, ...p ?? {} }), i.success(n.next === "IN" ? e("Checked in.") : e("Checked out.")), await c();
    } catch {
    }
  };
  return /* @__PURE__ */ t(K, { title: e("Check-in"), onBack: () => a(""), loading: o, error: l, onRetry: c, children: n && /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
    n.offered ? /* @__PURE__ */ h(de, { children: [
      r.errorMessage && /* @__PURE__ */ t(E, { tone: "error", children: r.errorMessage }),
      v && /* @__PURE__ */ t(E, { tone: "warning", children: e("Your phone did not share where you are. Allow location for this site if HR needs it.") }),
      /* @__PURE__ */ h(b, { size: "lg", loading: u || r.loading, onClick: d, children: [
        n.next === "IN" ? /* @__PURE__ */ t(fn, {}) : /* @__PURE__ */ t(vn, {}),
        n.next === "IN" ? e("Check In") : e("Check Out")
      ] }),
      n.location && /* @__PURE__ */ h(G, { size: "sm", muted: !0, children: [
        /* @__PURE__ */ t(Te, { "aria-hidden": !0, className: "mr-1 inline size-4" }),
        e("Where you are is recorded with each check-in, as HR asks.")
      ] })
    ] }) : /* @__PURE__ */ t(E, { tone: "info", children: e("HR has not turned on checking in from the phone.") }),
    /* @__PURE__ */ t(B, { title: e("Today"), children: n.today.length === 0 ? /* @__PURE__ */ t(G, { muted: !0, children: e("No check-ins today yet. Clock-ins on the office device show here too.") }) : /* @__PURE__ */ t(D, { divided: !0, children: n.today.map((p) => /* @__PURE__ */ t(
      L,
      {
        primary: p.log_type === "IN" ? e("In") : e("Out"),
        secondary: p.device_id ? e("{0} · {1}", [ve(p.time), p.device_id]) : ve(p.time)
      },
      p.name
    )) }) })
  ] }) });
}
function Sn() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.attendanceRequests);
  return /* @__PURE__ */ t(
    Z,
    {
      title: e("Attendance Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: l,
      actions: /* @__PURE__ */ h(b, { onClick: () => a(s.attendanceNew), children: [
        /* @__PURE__ */ t(se, {}),
        e("New Request")
      ] }),
      children: c && !i?.attendance.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Te, {}), title: e("No attendance requests"), description: e("Ask for days you worked from home or on duty elsewhere to count as attended.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i?.attendance ?? []).map((r) => /* @__PURE__ */ t(
        L,
        {
          primary: r.reason === "Work From Home" ? e("Work From Home") : e("On Duty"),
          secondary: e("{0} to {1}", [_(r.from_date), _(r.to_date)]),
          action: /* @__PURE__ */ t(M, { value: r.docstatus === 1 ? "Approved" : r.docstatus === 2 ? "Cancelled" : "Open" }),
          onClick: () => a(s.attendanceRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function Mn() {
  const a = A(), i = F(), n = S(g.requestAttendance), o = oe(() => ae.object({ from_date: me(() => e("From Date")), to_date: me(() => e("To Date")), reason: ye(() => e("Reason")) }).loose(), []), l = ie({
    schema: o,
    defaultValues: { from_date: Y(), to_date: Y(), reason: "Work From Home", explanation: "", half_day: !1 }
  }), c = l.watch("from_date");
  return /* @__PURE__ */ t(K, { title: e("New Attendance Request"), onBack: () => a(s.attendance), children: /* @__PURE__ */ h(
    re,
    {
      form: l,
      onSubmit: async (r) => {
        const u = await n.run({ ...r, half_day: r.half_day ? 1 : 0 });
        i.success(e("Request sent to HR.")), a(s.attendanceRecord(u));
      },
      children: [
        /* @__PURE__ */ t(
          Ge,
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
        /* @__PURE__ */ t(te, { name: "from_date", label: e("From Date"), required: !0 }),
        /* @__PURE__ */ t(te, { name: "to_date", label: e("To Date"), required: !0, minDate: c || void 0 }),
        /* @__PURE__ */ t(Ke, { name: "half_day", label: e("Half Day") }),
        /* @__PURE__ */ t(z, { name: "explanation", label: e("Explanation"), multiline: !0, rows: 3 }),
        /* @__PURE__ */ t(ue, { submitLabel: e("Send Request"), onCancel: () => a(s.attendance) })
      ]
    }
  ) });
}
function Fe({ doctype: a }) {
  const i = A(), n = X(U().name), { data: o, isLoading: l, error: c, mutate: r } = N(g.attendanceRecord, { doctype: a, name: n }), u = a === "Shift Request";
  return /* @__PURE__ */ t(
    J,
    {
      title: u ? e("Shift Request") : e("Attendance Request"),
      subtitle: o && (o.mine ? n : o.employee_name),
      meta: o && /* @__PURE__ */ t(M, { value: u ? o.status : o.docstatus === 1 ? "Approved" : "Open" }),
      onBack: () => i(u ? s.shifts : s.attendance),
      loading: l,
      error: c,
      onRetry: r,
      children: o && /* @__PURE__ */ t(
        j,
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
function Wn() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.attendanceRequests);
  return /* @__PURE__ */ t(
    Z,
    {
      title: e("Shift Requests"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: l,
      actions: /* @__PURE__ */ h(b, { onClick: () => a(s.shiftNew), children: [
        /* @__PURE__ */ t(se, {}),
        e("New Request")
      ] }),
      children: c && !i?.shifts.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Ct, {}), title: e("No shift requests"), description: e("Ask to work a different shift for some days.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i?.shifts ?? []).map((r) => /* @__PURE__ */ t(
        L,
        {
          primary: r.shift_type,
          secondary: r.to_date ? e("{0} to {1}", [_(r.from_date), _(r.to_date)]) : e("From {0}", [_(r.from_date)]),
          action: /* @__PURE__ */ t(M, { value: r.status }),
          onClick: () => a(s.shiftRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function qn() {
  const a = A(), i = F(), n = N(g.attendanceOptions), o = S(g.requestShift), l = oe(() => ae.object({ shift_type: ye(() => e("Shift Type")), from_date: me(() => e("From Date")) }).loose(), []), c = ie({ schema: l, defaultValues: { shift_type: "", from_date: Y(), to_date: "" } });
  return /* @__PURE__ */ h(K, { title: e("New Shift Request"), onBack: () => a(s.shifts), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    n.data && !n.data.has_shift_approver && /* @__PURE__ */ t(E, { tone: "warning", children: e("Nobody approves your shift requests yet. Ask HR to set a shift approver.") }),
    /* @__PURE__ */ h(
      re,
      {
        form: c,
        onSubmit: async (r) => {
          const u = await o.run({ shift_type: r.shift_type, from_date: r.from_date, to_date: r.to_date || void 0 });
          i.success(e("Request sent to {0}.", [n.data?.shift_approver_name ?? e("your shift approver")])), a(s.shiftRecord(u));
        },
        children: [
          /* @__PURE__ */ t(ge, { name: "shift_type", label: e("Shift Type"), required: !0, options: (n.data?.shift_types ?? []).map((r) => ({ value: r, label: r })) }),
          /* @__PURE__ */ t(te, { name: "from_date", label: e("From Date"), required: !0 }),
          /* @__PURE__ */ t(te, { name: "to_date", label: e("To Date"), hint: e("Leave empty if the shift carries on.") }),
          /* @__PURE__ */ t(ue, { submitLabel: e("Send Request"), onCancel: () => a(s.shifts) })
        ]
      }
    )
  ] });
}
function Ce(a, i, n) {
  return /* @__PURE__ */ t(D, { divided: !0, children: a.map((o) => /* @__PURE__ */ t(
    L,
    {
      primary: i ? e("Covered by {0}", [o.stand_in]) : o.employee_name,
      secondary: e("{0} to {1}", [_(o.leave_from), _(o.leave_to)]),
      action: /* @__PURE__ */ t(M, { value: o.waiting_for_me ? "Pending" : o.status }),
      onClick: () => n(s.handover(o.name))
    },
    o.name
  )) });
}
function $n() {
  const a = A(), [i, n] = T("to_answer"), { data: o, isLoading: l, error: c, mutate: r, hasLoaded: u } = N(g.cover), y = (v, m) => /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Nt, {}), title: v, description: m });
  return /* @__PURE__ */ h(Z, { title: e("Cover"), onBack: () => a(""), loading: l, error: c, onRetry: r, children: [
    /* @__PURE__ */ t(
      Vt,
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
    /* @__PURE__ */ t(ke, { id: "to_answer", value: i, children: u && !o?.to_answer.length ? y(e("Nobody has asked you to cover"), e("When a colleague names you as their stand-in, it shows here for you to agree or decline.")) : Ce(o?.to_answer ?? [], !1, a) }),
    /* @__PURE__ */ t(ke, { id: "covering", value: i, children: u && !o?.covering.length ? y(e("You are not covering anyone now"), e("Work you agreed to cover shows here while the person is away.")) : Ce(o?.covering ?? [], !1, a) }),
    /* @__PURE__ */ t(ke, { id: "mine", value: i, children: u && !o?.mine.length ? y(e("No handovers of your own"), e("When you apply for leave, the handover you send shows here.")) : Ce(o?.mine ?? [], !0, a) })
  ] });
}
function En() {
  const a = A(), i = F(), n = X(U().name), { data: o, isLoading: l, error: c, mutate: r } = N(g.handoverRecord, { name: n }), u = S(g.respond), y = S(g.respondAuthority), v = S(g.addNote), m = S(g.returnNote), d = S(g.returnWork), [p, R] = T(null), [x, H] = T(""), [f, q] = T(!1), [I, P] = T(!1), [ee, le] = T(null), w = async (C, qt) => {
    P(!0), le(null);
    try {
      await C(), i.success(qt), R(null), H(""), await r();
    } catch ($t) {
      le($t);
    } finally {
      P(!1);
    }
  }, O = o && o.can_answer ? /* @__PURE__ */ h("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(b, { variant: "outline", onClick: () => R({ kind: "decline" }), children: e("Decline") }),
    /* @__PURE__ */ t(b, { loading: I, onClick: () => w(() => u.run({ name: n, answer: "Accepted" }), e("You agreed to cover this.")), children: e("Accept") })
  ] }) : o && o.can_return ? /* @__PURE__ */ t(b, { onClick: () => q(!0), children: e("I'm Back") }) : void 0;
  return /* @__PURE__ */ h(
    J,
    {
      title: o ? o.is_owner ? e("My Handover") : e("Cover for {0}", [o.employee_name]) : e("Handover"),
      subtitle: o && e("{0} to {1}", [_(o.leave_from), _(o.leave_to)]),
      meta: o && /* @__PURE__ */ t(M, { value: o.status }),
      onBack: () => a(s.cover),
      actions: O,
      loading: l,
      error: c,
      onRetry: r,
      children: [
        o && /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
          ee ? /* @__PURE__ */ t(E, { tone: "error", children: u.errorMessage || y.errorMessage || d.errorMessage || e("That did not go through. Try again.") }) : null,
          /* @__PURE__ */ t(
            j,
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
          /* @__PURE__ */ t(B, { title: e("Work"), children: o.work.length === 0 ? /* @__PURE__ */ t(G, { muted: !0, children: e("No work items were handed over; the notes say what to look after.") }) : /* @__PURE__ */ t(D, { divided: !0, children: o.work.map((C) => /* @__PURE__ */ t(
            L,
            {
              primary: C.description,
              secondary: [C.covered_by, C.due_date ? e("Due {0}", [_(C.due_date)]) : "", C.notes ?? ""].filter(Boolean).join(" · "),
              action: C.mine && o.status === "Active" ? /* @__PURE__ */ t(b, { variant: "ghost", onClick: () => R({ kind: "note", row: C.row, text: C.notes ?? "" }), children: e("Leave a Note") }) : C.progress || C.acceptance ? /* @__PURE__ */ t(M, { value: C.progress || C.acceptance }) : void 0
            },
            C.row
          )) }) }),
          o.approvals.length > 0 && /* @__PURE__ */ t(B, { title: e("Approvals"), children: /* @__PURE__ */ t(D, { divided: !0, children: o.approvals.map((C) => /* @__PURE__ */ t(
            L,
            {
              primary: C.label,
              secondary: C.covered_by,
              action: C.mine && o.can_answer && C.acceptance === "Pending" ? /* @__PURE__ */ h("div", { className: "flex gap-1", children: [
                /* @__PURE__ */ t(b, { variant: "ghost", onClick: () => R({ kind: "decline-approval", row: C.row }), children: e("Decline") }),
                /* @__PURE__ */ t(
                  b,
                  {
                    variant: "ghost",
                    onClick: () => w(() => y.run({ name: n, row: C.row, answer: "Accepted" }), e("You agreed to approve in their place.")),
                    children: e("Accept")
                  }
                )
              ] }) : C.acceptance ? /* @__PURE__ */ t(M, { value: C.acceptance }) : void 0
            },
            C.row
          )) }) }),
          o.is_stand_in && o.status === "Active" && /* @__PURE__ */ t(b, { variant: "outline", onClick: () => R({ kind: "return-note" }), children: e("Note for Return") })
        ] }),
        /* @__PURE__ */ t(
          et,
          {
            open: !!p,
            onClose: () => R(null),
            title: p?.kind === "note" ? e("Leave a Note") : p?.kind === "return-note" ? e("Note for Return") : e("Decline"),
            description: p?.kind === "note" ? e("What you did on this piece of work, for when they are back.") : p?.kind === "return-note" ? e("What they should know on their first day back.") : e("Say why you cannot cover it, so they can ask someone else."),
            actions: /* @__PURE__ */ h(de, { children: [
              /* @__PURE__ */ t(b, { variant: "outline", onClick: () => R(null), children: e("Cancel") }),
              /* @__PURE__ */ t(
                b,
                {
                  loading: I,
                  disabled: !(p?.kind === "note" ? p.text : x).trim(),
                  onClick: () => {
                    p && (p.kind === "decline" ? w(() => u.run({ name: n, answer: "Declined", reason: x }), e("You declined.")) : p.kind === "decline-approval" ? w(() => y.run({ name: n, row: p.row, answer: "Declined", reason: x }), e("You declined.")) : p.kind === "note" ? w(() => v.run({ name: n, row: p.row, note: p.text }), e("Note saved.")) : w(() => m.run({ name: n, note: x }), e("Note saved.")));
                  },
                  children: p?.kind === "decline" || p?.kind === "decline-approval" ? e("Decline") : e("Save Note")
                }
              )
            ] }),
            children: /* @__PURE__ */ t(
              Ut,
              {
                "aria-label": e("Note"),
                rows: 4,
                value: p?.kind === "note" ? p.text : x,
                onChange: (C) => p?.kind === "note" ? R({ ...p, text: C.target.value }) : H(C.target.value)
              }
            )
          }
        ),
        /* @__PURE__ */ t(
          tt,
          {
            open: f,
            onClose: () => q(!1),
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
function Tn() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l } = N(g.home), c = s.week(He(Y())), r = [
    { label: e("Leave"), hint: e("Apply, and see what you asked for"), path: s.leave, icon: /* @__PURE__ */ t(De, {}) },
    { label: e("Cover"), hint: e("Handovers to answer and work you cover"), path: s.cover, icon: /* @__PURE__ */ t(Nt, {}) },
    { label: e("Time Off in Lieu"), hint: e("Claim extra hours as time off"), path: s.toil, icon: /* @__PURE__ */ t(Se, {}) },
    { label: e("Timesheets"), hint: e("Your week, day by day"), path: s.timesheet, icon: /* @__PURE__ */ t(Le, {}) },
    { label: e("Expense Claims"), hint: e("Claims and receipts"), path: s.expenses, icon: /* @__PURE__ */ t(Me, {}) },
    { label: e("Advances"), hint: e("Money paid ahead and what is left to settle"), path: s.advances, icon: /* @__PURE__ */ t(pt, {}) },
    { label: e("Payslips"), hint: e("Your pay, month by month"), path: s.pay, icon: /* @__PURE__ */ t(Dt, {}) },
    { label: e("Attendance Requests"), hint: e("Days worked away from the office"), path: s.attendance, icon: /* @__PURE__ */ t(Te, {}) },
    { label: e("Shift Requests"), hint: e("Ask to work another shift"), path: s.shifts, icon: /* @__PURE__ */ t(Ct, {}) },
    { label: e("My Details"), hint: e("Contact, dependants and where you are paid"), path: s.me, icon: /* @__PURE__ */ t(yn, {}) }
  ];
  return i?.checkin.offered && r.splice(4, 0, { label: e("Check-in"), hint: e("Check in and out from your phone"), path: s.checkIn, icon: /* @__PURE__ */ t(Pe, {}) }), /* @__PURE__ */ t(Jt, { title: e("My HR"), subtitle: i?.employee.employee_name, loading: n, error: o, onRetry: l, children: /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
    i && i.balances.length > 0 && /* @__PURE__ */ t(nt, { columns: 2, children: i.balances.map((u) => /* @__PURE__ */ t(xe, { label: u.label, value: e("{0} days", [String(u.value)]), onClick: () => a(u.key.startsWith("toil") ? s.toil : s.leave) }, u.key)) }),
    /* @__PURE__ */ t(B, { title: e("Quick Actions"), children: /* @__PURE__ */ h("div", { className: "grid grid-cols-1 gap-2 sm:grid-cols-2", children: [
      /* @__PURE__ */ h(b, { variant: "outline", onClick: () => a(s.leaveNew), children: [
        /* @__PURE__ */ t(De, {}),
        e("Apply for Leave")
      ] }),
      /* @__PURE__ */ h(b, { variant: "outline", onClick: () => a(s.toilNew), children: [
        /* @__PURE__ */ t(Se, {}),
        e("Claim Time Off")
      ] }),
      /* @__PURE__ */ h(b, { variant: "outline", onClick: () => a(c), children: [
        /* @__PURE__ */ t(pn, {}),
        e("This Week's Timesheet")
      ] }),
      /* @__PURE__ */ h(b, { variant: "outline", onClick: () => a(s.expenseNew), children: [
        /* @__PURE__ */ t(Me, {}),
        e("New Expense Claim")
      ] }),
      i?.checkin.offered && /* @__PURE__ */ h(b, { variant: "outline", onClick: () => a(s.checkIn), children: [
        /* @__PURE__ */ t(Pe, {}),
        e("Check In")
      ] })
    ] }) }),
    i && i.in_flight.length > 0 && /* @__PURE__ */ t(B, { title: e("In Progress"), children: /* @__PURE__ */ t(D, { divided: !0, children: i.in_flight.map((u) => {
      const y = Xt(u.doctype);
      return /* @__PURE__ */ t(L, { primary: u.label, action: /* @__PURE__ */ t(he, { children: u.count }), onClick: y ? () => a(y) : void 0 }, u.key);
    }) }) }),
    /* @__PURE__ */ t(B, { title: e("Everything in My HR"), children: /* @__PURE__ */ t(D, { divided: !0, children: r.map((u) => /* @__PURE__ */ t(L, { primary: u.label, secondary: u.hint, icon: u.icon, action: /* @__PURE__ */ t(st, { "aria-hidden": !0 }), onClick: () => a(u.path) }, u.path)) }) })
  ] }) });
}
function Hn(a) {
  return { show: !!a?.needed, standInRequired: !!a?.needed && !!a?.required };
}
function Bn(a, i) {
  const n = a.filter((c) => c.work_date), o = new Set(n.map((c) => c.work_date)), l = i.filter((c) => !o.has(c.work_date)).map((c) => ({ work_date: c.work_date, hours: c.hours, work_done: "" }));
  return [...n, ...l].sort((c, r) => c.work_date.localeCompare(r.work_date));
}
function Pn(a) {
  if (a.change === "Mobile Money") return a.mobile_no?.trim() ? [] : ["mobile_no"];
  const i = ["bank", "bank_account_no", "account_name"].filter((n) => !a[n]?.trim());
  return a.evidence ? i : [...i, "evidence"];
}
function On() {
  const a = A(), [i, n] = T("all"), { data: o, isLoading: l, error: c, mutate: r, hasLoaded: u } = N(g.leaveList), y = o ?? [], v = y.filter((d) => d.status === "Open" && d.docstatus === 0), m = i === "open" ? v : i === "decided" ? y.filter((d) => !v.includes(d)) : y;
  return /* @__PURE__ */ t(
    Z,
    {
      title: e("Leave"),
      onBack: () => a(""),
      loading: l,
      error: c,
      onRetry: r,
      actions: /* @__PURE__ */ h(b, { onClick: () => a(s.leaveNew), children: [
        /* @__PURE__ */ t(se, {}),
        e("Apply for Leave")
      ] }),
      toolbar: /* @__PURE__ */ t(
        Gt,
        {
          label: e("Show"),
          value: i,
          onChange: n,
          options: [
            { value: "all", label: e("All"), count: y.length },
            { value: "open", label: e("Waiting"), count: v.length },
            { value: "decided", label: e("Decided"), count: y.length - v.length }
          ]
        }
      ),
      children: u && m.length === 0 ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(De, {}), title: e("No leave here"), description: e("Leave you apply for shows here until it is decided, and after.") }) : /* @__PURE__ */ t(D, { divided: !0, children: m.map((d) => /* @__PURE__ */ t(
        L,
        {
          primary: d.leave_type,
          secondary: d.handover ? e("{0} to {1} · {2} days · covered by {3}", [_(d.from_date), _(d.to_date), String(d.total_leave_days), d.handover.stand_in]) : e("{0} to {1} · {2} days", [_(d.from_date), _(d.to_date), String(d.total_leave_days)]),
          action: /* @__PURE__ */ t(M, { value: d.status }),
          onClick: () => a(s.leaveRecord(d.name))
        },
        d.name
      )) })
    }
  );
}
function Fn() {
  const a = A(), i = F(), [n] = Ue(), o = oe(
    () => ae.object({
      leave_type: ye(() => e("Leave Type")),
      from_date: me(() => e("From Date")),
      to_date: me(() => e("To Date"))
    }),
    []
  ), l = ie({
    schema: o.passthrough(),
    defaultValues: { leave_type: n.get("type") ?? "", from_date: "", to_date: "", half_day: !1, description: "", stand_in: "", handover_notes: "", todos: [], approvals: [] }
  }), [c, r, u, y] = l.watch(["leave_type", "from_date", "to_date", "half_day"]), v = !!(c && r && u), m = N(g.leaveOptions, v ? { leave_type: c, from_date: r, to_date: u, half_day: y ? 1 : 0 } : {}), d = N(g.colleagues, {}, { enabled: !!m.data?.handover.needed }), p = S(g.applyForLeave), R = Hn(v ? m.data?.handover : void 0), x = m.data?.leave_types.find((f) => f.name === c), H = async (f) => {
    if (R.standInRequired && !f.stand_in) return { errors: { stand_in: e("Your company asks for cover on this leave. Choose who will cover your work.") } };
    const q = await p.run({
      leave_type: f.leave_type,
      from_date: f.from_date,
      to_date: f.to_date,
      half_day: f.half_day ? 1 : 0,
      description: f.description,
      stand_in: R.show && f.stand_in || void 0,
      handover_notes: f.handover_notes,
      todos: JSON.stringify(f.todos),
      approvals: JSON.stringify(f.approvals)
    });
    i.success(q.handover ? e("Leave applied for, and the handover sent to your stand-in.") : e("Leave applied for.")), a(s.leaveRecord(q.name));
  };
  return /* @__PURE__ */ t(K, { title: e("Apply for Leave"), onBack: () => a(s.leave), loading: m.isLoading && !m.data && !v, error: m.hasLoaded && !v ? m.error : void 0, children: /* @__PURE__ */ t(re, { form: l, onSubmit: H, children: /* @__PURE__ */ t(
    It,
    {
      submitLabel: e("Apply"),
      steps: [
        {
          id: "leave",
          title: e("Leave"),
          fields: ["leave_type", "from_date", "to_date"],
          content: /* @__PURE__ */ h("div", { className: "flex flex-col gap-4", children: [
            /* @__PURE__ */ t(
              ge,
              {
                name: "leave_type",
                label: e("Leave Type"),
                required: !0,
                options: (m.data?.leave_types ?? []).map((f) => ({
                  value: f.name,
                  label: f.name,
                  description: f.left === null ? e("Unpaid") : e("{0} days left", [String(f.left)])
                })),
                hint: x && x.left !== null ? e("{0} days left", [String(x.left)]) : void 0
              }
            ),
            /* @__PURE__ */ t(te, { name: "from_date", label: e("From Date"), required: !0 }),
            /* @__PURE__ */ t(te, { name: "to_date", label: e("To Date"), required: !0, minDate: r || void 0 }),
            /* @__PURE__ */ t(Ke, { name: "half_day", label: e("Half Day"), hint: e("Only the first day is a half day.") }),
            /* @__PURE__ */ t(z, { name: "description", label: e("Reason"), multiline: !0, rows: 3 }),
            v && m.data && /* @__PURE__ */ t(E, { tone: "info", children: m.data.days !== null ? e("{0} days, approved by {1}.", [String(m.data.days), m.data.approver_name ?? e("your leave approver")]) : e("Approved by {0}.", [m.data.approver_name ?? e("your leave approver")]) })
          ] })
        },
        {
          id: "handover",
          title: e("Handover"),
          visible: R.show,
          fields: ["stand_in"],
          description: R.standInRequired ? e("Your company asks for cover on leave like this. Your stand-in is asked to agree before the leave is approved.") : e("Your company suggests arranging cover. You can leave this out."),
          content: /* @__PURE__ */ h("div", { className: "flex flex-col gap-4", children: [
            /* @__PURE__ */ t(
              _e,
              {
                name: "stand_in",
                label: e("Stand-in"),
                required: R.standInRequired,
                options: (d.data ?? []).map((f) => ({ value: f.name, label: f.employee_name })),
                hint: e("A colleague in your company who is not away at the same time.")
              }
            ),
            /* @__PURE__ */ t(z, { name: "handover_notes", label: e("Handover Notes"), multiline: !0, rows: 4, hint: e("What your stand-in needs to know.") }),
            (m.data?.work.length ?? 0) > 0 && /* @__PURE__ */ t(
              _e,
              {
                name: "todos",
                multiple: !0,
                label: e("Work to Hand Over"),
                options: (m.data?.work ?? []).map((f) => ({ value: f.todo, label: f.description, description: f.due_date ? e("Due {0}", [_(f.due_date)]) : void 0 })),
                hint: e("Open items on your work list. Your stand-in gets them while you are away.")
              }
            ),
            (m.data?.approvals.length ?? 0) > 0 && /* @__PURE__ */ t(
              _e,
              {
                name: "approvals",
                multiple: !0,
                label: e("Approvals to Hand Over"),
                options: (m.data?.approvals ?? []).map((f) => ({ value: f.authority, label: f.authority_label })),
                hint: e("Your stand-in approves these in your place, once they agree.")
              }
            )
          ] })
        }
      ]
    }
  ) }) });
}
function In() {
  const a = A(), i = X(U().name), { data: n, isLoading: o, error: l, mutate: c } = N(g.leaveRecord, { name: i });
  return /* @__PURE__ */ t(
    J,
    {
      title: n ? n.leave_type : e("Leave"),
      subtitle: n && !n.mine ? n.employee_name : i,
      meta: n && /* @__PURE__ */ t(M, { value: n.status }),
      onBack: () => a(s.leave),
      loading: o,
      error: l,
      onRetry: c,
      children: n && /* @__PURE__ */ h("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          j,
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
        n.handover ? /* @__PURE__ */ t(D, { divided: !0, children: /* @__PURE__ */ t(
          L,
          {
            primary: e("Handover to {0}", [n.handover.stand_in]),
            action: /* @__PURE__ */ t(M, { value: n.handover.status }),
            onClick: () => a(s.handover(n.handover.name))
          }
        ) }) : /* @__PURE__ */ t(G, { muted: !0, children: e("No handover for this leave.") })
      ] })
    }
  );
}
class Mt extends Error {
  constructor() {
    super(...arguments);
    Be(this, "name", "VerificationCancelled");
  }
}
function qe(a, i = 0) {
  if (!a || typeof a != "object" || i > 3) return !1;
  const n = a;
  return n.exc_type === "VerificationNeeded" || typeof n.exception == "string" && n.exception.includes("VerificationNeeded") ? !0 : qe(n.payload, i + 1) || qe(n.original, i + 1);
}
async function Wt(a, i) {
  try {
    return await a();
  } catch (n) {
    if (!qe(n)) throw n;
    if (!await i()) throw new Mt();
    return a();
  }
}
function zn() {
  const a = A(), i = F(), { data: n, isLoading: o, error: l, mutate: c } = N(g.myDetails), r = S(g.updateMyContact), [u, y] = T(!1), [v, m] = T("");
  return /* @__PURE__ */ h(J, { title: e("My Details"), subtitle: n?.employee.employee_name, onBack: () => a(""), loading: o, error: l, onRetry: c, children: [
    n && /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
      /* @__PURE__ */ t(
        j,
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
      /* @__PURE__ */ h(
        B,
        {
          title: e("Contact"),
          action: n.has_contact ? /* @__PURE__ */ t(b, { variant: "outline", onClick: () => y(!0), children: e("Change Mobile Number") }) : void 0,
          children: [
            /* @__PURE__ */ t(j, { items: [{ label: e("Mobile No."), value: n.mobile_no ?? e("None yet") }] }),
            !n.has_contact && /* @__PURE__ */ t(G, { muted: !0, children: e("HR has not linked a contact to your record yet; ask them to.") })
          ]
        }
      ),
      /* @__PURE__ */ t(B, { title: e("Dependants and Beneficiaries"), children: n.dependants.length === 0 ? /* @__PURE__ */ t(G, { muted: !0, children: e("None recorded. HR records dependants and beneficiaries.") }) : /* @__PURE__ */ t(D, { divided: !0, children: n.dependants.map((d) => /* @__PURE__ */ t(L, { primary: d.full_name, secondary: [d.relationship, d.type, d.dob ? _(d.dob) : ""].filter(Boolean).join(" · ") }, d.name)) }) }),
      /* @__PURE__ */ h(
        B,
        {
          title: e("Payout Details"),
          subtitle: e("Where your pay goes. Only the last four digits are shown."),
          action: /* @__PURE__ */ t(b, { disabled: !!n.payout_request, onClick: () => a(s.payoutNew), children: e("Request a Change") }),
          children: [
            /* @__PURE__ */ t(
              j,
              {
                items: [
                  { label: e("Bank"), value: n.payout.bank ?? e("None") },
                  { label: e("Account No."), value: n.payout.account_no, hideWhenEmpty: !0 },
                  { label: e("Account Name"), value: n.payout.account_name, hideWhenEmpty: !0 },
                  { label: e("Mobile Money"), value: n.payout.mobile_no ?? e("None") }
                ]
              }
            ),
            n.payout_requests.length > 0 && /* @__PURE__ */ t(D, { divided: !0, children: n.payout_requests.map((d) => /* @__PURE__ */ t(
              L,
              {
                primary: d.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
                secondary: ve(d.creation),
                action: /* @__PURE__ */ t(M, { value: d.status }),
                onClick: () => a(s.payoutRecord(d.name))
              },
              d.name
            )) })
          ]
        }
      )
    ] }),
    /* @__PURE__ */ t(
      et,
      {
        open: u,
        onClose: () => y(!1),
        title: e("Change Mobile Number"),
        description: e("Your contact number at work. Where your pay goes changes only by a request to HR."),
        actions: /* @__PURE__ */ h(de, { children: [
          /* @__PURE__ */ t(b, { variant: "outline", onClick: () => y(!1), children: e("Cancel") }),
          /* @__PURE__ */ t(
            b,
            {
              loading: r.loading,
              disabled: !v.trim(),
              onClick: async () => {
                try {
                  await r.run({ mobile_no: v }), i.success(e("Mobile number changed.")), y(!1), m(""), await c();
                } catch {
                }
              },
              children: e("Save")
            }
          )
        ] }),
        children: /* @__PURE__ */ h("div", { className: "flex flex-col gap-2", children: [
          r.errorMessage && /* @__PURE__ */ t(E, { tone: "error", children: r.errorMessage }),
          /* @__PURE__ */ t(fe, { htmlFor: "new-mobile", children: e("New Mobile No.") }),
          /* @__PURE__ */ t(Ne, { id: "new-mobile", type: "tel", inputMode: "tel", autoComplete: "tel", value: v, onChange: (d) => m(d.target.value) })
        ] })
      }
    )
  ] });
}
function jn() {
  const a = A(), i = $e(), n = F(), o = N(g.payoutOptions), l = S(g.requestPayoutChange), c = S(g.setPayoutEvidence), r = S(g.sendPayoutChange), u = ie({
    defaultValues: { change: "Bank Account", bank: "", bank_account_no: "", branch_code: "", account_name: "", mobile_no: "", evidence: null, reason: "" }
  }), y = u.watch("change"), v = oe(
    () => ({ bank: e("Bank"), bank_account_no: e("Account No."), account_name: e("Account Name"), mobile_no: e("Mobile No."), evidence: e("Evidence") }),
    []
  ), m = async (d) => {
    const p = Pn(d);
    if (p.length) return { errors: Object.fromEntries(p.map((x) => [x, e("{0} is needed.", [v[x]])])) };
    const R = await l.run({
      change: d.change,
      bank: d.change === "Bank Account" ? d.bank : void 0,
      bank_account_no: d.change === "Bank Account" ? d.bank_account_no : void 0,
      branch_code: d.change === "Bank Account" ? d.branch_code : void 0,
      account_name: d.change === "Bank Account" ? d.account_name : void 0,
      mobile_no: d.change === "Mobile Money" ? d.mobile_no : void 0,
      reason: d.reason
    });
    if (d.change === "Bank Account" && d.evidence) {
      const x = await Je(d.evidence, { doctype: "Payout Change Request", docname: R, fieldname: "evidence", isPrivate: !0 });
      await c.run({ name: R, file_url: x.file_url });
    }
    try {
      await Wt(() => r.run({ name: R }), i.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it."));
    } catch (x) {
      if (!(x instanceof Mt)) throw x;
      n.info(e("Saved, not sent. Open it from My Details to send it."));
    }
    a(s.payoutRecord(R));
  };
  return /* @__PURE__ */ h(K, { title: e("Request a Change"), subtitle: e("Where your pay goes"), onBack: () => a(s.me), loading: o.isLoading, error: o.error, onRetry: o.mutate, children: [
    /* @__PURE__ */ t(E, { tone: "info", children: e("HR confirms every change before any pay goes there. We also tell your current number and email, in case this was not you.") }),
    /* @__PURE__ */ h(re, { form: u, onSubmit: m, children: [
      /* @__PURE__ */ t(
        Ge,
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
      y === "Bank Account" ? /* @__PURE__ */ h(de, { children: [
        /* @__PURE__ */ t(ge, { name: "bank", label: e("Bank"), required: !0, options: (o.data?.banks ?? []).map((d) => ({ value: d, label: d })) }),
        /* @__PURE__ */ t(z, { name: "bank_account_no", label: e("Account No."), required: !0 }),
        /* @__PURE__ */ t(z, { name: "branch_code", label: e("Branch") }),
        /* @__PURE__ */ t(z, { name: "account_name", label: e("Account Name"), required: !0, hint: e("As the bank has it. It must be in your own name.") }),
        /* @__PURE__ */ t(Ze, { name: "evidence", label: e("Evidence"), required: !0, upload: !1, accept: "image/*,application/pdf", hint: e("A bank letter or the top of a statement, showing the account in your name.") })
      ] }) : /* @__PURE__ */ t(zt, { name: "mobile_no", label: e("Mobile No."), required: !0, hint: e("The number your pay should go to by mobile money.") }),
      /* @__PURE__ */ t(z, { name: "reason", label: e("Reason"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(ue, { submitLabel: e("Send to HR"), onCancel: () => a(s.me), dirtyHint: !1 })
    ] })
  ] });
}
function Yn() {
  const a = A(), i = $e(), n = F(), o = X(U().name), { data: l, isLoading: c, error: r, mutate: u } = N(g.payoutRequestRecord, { name: o }), y = S(g.sendPayoutChange), v = S(g.withdrawPayoutChange), [m, d] = T(!1), p = async () => {
    try {
      await Wt(() => y.run({ name: o }), i.verify), n.success(e("Sent to HR. Nothing changes until HR confirms it.")), await u();
    } catch {
    }
  }, R = l?.mine && l.status === "Draft" ? /* @__PURE__ */ t(b, { loading: y.loading, onClick: p, children: e("Send to HR") }) : l?.mine && l.status === "Waiting for HR" ? /* @__PURE__ */ t(b, { variant: "outline", onClick: () => d(!0), children: e("Withdraw") }) : void 0;
  return /* @__PURE__ */ h(
    J,
    {
      title: l?.change === "Mobile Money" ? e("Change to Mobile Money") : e("Change of Bank Account"),
      subtitle: o,
      meta: l && /* @__PURE__ */ t(M, { value: l.status }),
      onBack: () => a(s.me),
      actions: R,
      loading: c,
      error: r,
      onRetry: u,
      children: [
        l && /* @__PURE__ */ h("div", { className: "flex flex-col gap-4", children: [
          y.errorMessage && /* @__PURE__ */ t(E, { tone: "error", children: y.errorMessage }),
          l.status === "Waiting for HR" && /* @__PURE__ */ t(E, { tone: "info", children: e("HR confirms it on the desk. You are told either way.") }),
          /* @__PURE__ */ t(
            j,
            {
              items: [
                { label: e("Bank"), value: l.bank, hideWhenEmpty: !0 },
                { label: e("Account No."), value: l.account_no, hideWhenEmpty: !0 },
                { label: e("Account Name"), value: l.account_name, hideWhenEmpty: !0 },
                { label: e("Mobile No."), value: l.mobile_no, hideWhenEmpty: !0 },
                { label: e("Provider"), value: l.provider, hideWhenEmpty: !0 },
                { label: e("Evidence"), value: l.change === "Bank Account" ? l.has_evidence ? e("Attached") : e("Missing") : null, hideWhenEmpty: !0 },
                { label: e("Sent On"), value: l.sent_on ? ve(l.sent_on) : null, hideWhenEmpty: !0 },
                { label: e("Effective From"), value: l.effective_from ? _(l.effective_from) : null, hideWhenEmpty: !0 },
                { label: e("Decision Note"), value: l.decision_note, hideWhenEmpty: !0, full: !0 },
                { label: e("Reason"), value: l.reason, hideWhenEmpty: !0, full: !0 }
              ]
            }
          )
        ] }),
        /* @__PURE__ */ t(
          tt,
          {
            open: m,
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
function Vn() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.expenseList);
  return /* @__PURE__ */ t(
    Z,
    {
      title: e("Expense Claims"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: l,
      actions: /* @__PURE__ */ h(b, { onClick: () => a(s.expenseNew), children: [
        /* @__PURE__ */ t(se, {}),
        e("New Expense Claim")
      ] }),
      children: c && !i?.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Me, {}), title: e("No expense claims yet"), description: e("Claim what you spent for work, with a photo of each receipt.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i ?? []).map((r) => /* @__PURE__ */ t(
        L,
        {
          primary: $(r.total_claimed_amount, r.currency),
          secondary: _(r.posting_date || r.creation),
          action: /* @__PURE__ */ t(M, { value: r.docstatus === 0 ? r.approval_status || "Draft" : r.status }),
          onClick: () => a(s.expenseRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function Un() {
  const a = A(), i = F(), n = N(g.expenseOptions), o = S(g.claimExpenses), l = oe(
    () => ae.object({
      lines: ae.array(ae.object({ expense_type: ye(() => e("Expense Type")), amount: Qe(() => e("Amount"), { min: 0.01 }) }).loose()).min(1)
    }).loose(),
    []
  ), c = ie({ schema: l, defaultValues: { lines: [{ expense_date: Y(), expense_type: "", amount: null, description: "" }], remark: "", receipts: [] } }), r = async (u) => {
    const y = await o.run({ lines: JSON.stringify(u.lines), remark: u.remark }), v = [];
    for (const m of u.receipts ?? [])
      try {
        await Je(m, { doctype: "Expense Claim", docname: y, isPrivate: !0 });
      } catch {
        v.push(m.name);
      }
    v.length ? i.warning(e("The claim was saved, but {0} receipts did not upload. Add them on a computer.", [String(v.length)])) : i.success(e("Claim sent to {0}.", [n.data?.approver_name ?? e("your expense approver")])), a(s.expenseRecord(y));
  };
  return /* @__PURE__ */ h(K, { title: e("New Expense Claim"), onBack: () => a(s.expenses), loading: n.isLoading, error: n.error, onRetry: n.mutate, children: [
    n.data && !n.data.approver_name && /* @__PURE__ */ t(E, { tone: "warning", children: e("Nobody approves your expense claims yet. Ask HR to set an expense approver.") }),
    /* @__PURE__ */ h(re, { form: c, onSubmit: r, children: [
      /* @__PURE__ */ t(
        Xe,
        {
          name: "lines",
          label: e("Expenses"),
          minRows: 1,
          addLabel: e("Add an Expense"),
          newRow: () => ({ expense_date: Y(), expense_type: "", amount: null, description: "" }),
          renderRow: (u) => /* @__PURE__ */ h(de, { children: [
            /* @__PURE__ */ t(ge, { name: u("expense_type"), label: e("Expense Type"), required: !0, options: (n.data?.types ?? []).map((y) => ({ value: y.name, label: y.name, description: y.description ?? void 0 })) }),
            /* @__PURE__ */ t(Ee, { name: u("amount"), label: e("Amount ({0})", [n.data?.currency ?? ""]), required: !0, min: 0, step: 0.01 }),
            /* @__PURE__ */ t(te, { name: u("expense_date"), label: e("Date"), maxDate: Y() }),
            /* @__PURE__ */ t(z, { name: u("description"), label: e("Description") })
          ] })
        }
      ),
      /* @__PURE__ */ t(Ze, { name: "receipts", label: e("Receipts"), multiple: !0, upload: !1, accept: "image/*,application/pdf", hint: e("Take a photo of each receipt, or choose a file. Only you, your approver and HR can open them.") }),
      /* @__PURE__ */ t(z, { name: "remark", label: e("Note"), multiline: !0, rows: 2 }),
      /* @__PURE__ */ t(ue, { submitLabel: e("Send Claim"), onCancel: () => a(s.expenses) })
    ] })
  ] });
}
function Jn() {
  const a = A(), i = X(U().name), { data: n, isLoading: o, error: l, mutate: c } = N(g.expenseRecord, { name: i });
  return /* @__PURE__ */ t(
    J,
    {
      title: n ? $(n.total_claimed_amount, n.currency) : e("Expense Claim"),
      subtitle: n && (n.mine ? i : n.employee_name),
      meta: n && /* @__PURE__ */ t(M, { value: n.docstatus === 0 ? n.approval_status || "Draft" : n.status }),
      onBack: () => a(s.expenses),
      loading: o,
      error: l,
      onRetry: c,
      children: n && /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
        /* @__PURE__ */ t(
          j,
          {
            items: [
              { label: e("Claimed"), value: $(n.total_claimed_amount, n.currency) },
              { label: e("Approved Amount"), value: n.docstatus === 1 ? $(n.total_sanctioned_amount, n.currency) : null, hideWhenEmpty: !0 },
              { label: e("Expense Approver"), value: n.approver_name, hideWhenEmpty: !0 },
              { label: e("Note"), value: n.remark, hideWhenEmpty: !0, full: !0 }
            ]
          }
        ),
        /* @__PURE__ */ t(B, { title: e("Expenses"), children: /* @__PURE__ */ t(D, { divided: !0, children: n.expenses.map((r, u) => /* @__PURE__ */ t(L, { primary: `${r.expense_type} · ${$(r.amount, n.currency)}`, secondary: [_(r.expense_date), r.description ?? ""].filter(Boolean).join(" · ") }, u)) }) }),
        n.receipts.length > 0 && /* @__PURE__ */ t(B, { title: e("Receipts"), children: /* @__PURE__ */ t(D, { divided: !0, children: n.receipts.map((r) => /* @__PURE__ */ t(L, { primary: r.file_name, href: r.file_url }, r.name)) }) })
      ] })
    }
  );
}
function Gn() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.advanceList);
  return /* @__PURE__ */ t(
    Z,
    {
      title: e("Advances"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: l,
      actions: /* @__PURE__ */ h(b, { onClick: () => a(s.advanceNew), children: [
        /* @__PURE__ */ t(se, {}),
        e("Request an Advance")
      ] }),
      children: c && !i?.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(pt, {}), title: e("No advances"), description: e("Money paid to you ahead of work shows here, with what is left to settle.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i ?? []).map((r) => /* @__PURE__ */ t(
        L,
        {
          primary: r.purpose,
          secondary: r.to_settle > 0 ? e("{0} · {1} left to settle", [$(r.advance_amount, r.currency), $(r.to_settle, r.currency)]) : $(r.advance_amount, r.currency),
          action: /* @__PURE__ */ t(M, { value: r.docstatus === 0 ? "Draft" : r.status }),
          onClick: () => a(s.advanceRecord(r.name))
        },
        r.name
      )) })
    }
  );
}
function Kn() {
  const a = A(), i = F(), n = S(g.requestAdvance), o = oe(() => ae.object({ purpose: ye(() => e("Purpose")), amount: Qe(() => e("Amount"), { min: 1 }) }), []), l = ie({ schema: o, defaultValues: { purpose: "", amount: null } });
  return /* @__PURE__ */ t(K, { title: e("Request an Advance"), onBack: () => a(s.advances), children: /* @__PURE__ */ h(
    re,
    {
      form: l,
      onSubmit: async (c) => {
        const r = await n.run({ purpose: c.purpose, amount: c.amount });
        i.success(e("Advance requested.")), a(s.advanceRecord(r));
      },
      children: [
        /* @__PURE__ */ t(z, { name: "purpose", label: e("Purpose"), required: !0, multiline: !0, rows: 2, hint: e("What the money is for, e.g. a field visit.") }),
        /* @__PURE__ */ t(Ee, { name: "amount", label: e("Amount"), required: !0, min: 1, step: 1 }),
        /* @__PURE__ */ t(ue, { submitLabel: e("Request"), onCancel: () => a(s.advances) })
      ]
    }
  ) });
}
function Zn() {
  const a = A(), i = X(U().name), { data: n, isLoading: o, error: l, mutate: c } = N(g.advanceRecord, { name: i });
  return /* @__PURE__ */ t(
    J,
    {
      title: n?.purpose ?? e("Advance"),
      subtitle: n && (n.mine ? i : n.employee_name),
      meta: n && /* @__PURE__ */ t(M, { value: n.docstatus === 0 ? "Draft" : n.status }),
      onBack: () => a(s.advances),
      loading: o,
      error: l,
      onRetry: c,
      children: n && /* @__PURE__ */ t(
        j,
        {
          items: [
            { label: e("Amount"), value: $(n.advance_amount, n.currency) },
            { label: e("Paid"), value: $(n.paid_amount, n.currency) },
            { label: e("Claimed"), value: $(n.claimed_amount, n.currency) },
            { label: e("Returned"), value: $(n.return_amount, n.currency) },
            { label: e("Left to Settle"), value: $(n.to_settle, n.currency) },
            { label: e("Requested On"), value: _(n.posting_date) }
          ]
        }
      )
    }
  );
}
function Qn() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.payslips);
  return /* @__PURE__ */ t(Z, { title: e("Payslips"), onBack: () => a(""), loading: n, error: o, onRetry: l, children: c && !i?.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Dt, {}), title: e("No payslips yet"), description: e("Your payslips show here once payroll is run.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i ?? []).map((r) => /* @__PURE__ */ t(
    L,
    {
      primary: e("{0} to {1}", [_(r.start_date), _(r.end_date)]),
      secondary: e("Net pay {0}", [$(r.net_pay, r.currency)]),
      onClick: () => a(s.payRecord(r.name))
    },
    r.name
  )) }) });
}
function Xn() {
  const a = A(), i = X(U().name), { data: n, isLoading: o, error: l, mutate: c } = N(g.payslipRecord, { name: i });
  return /* @__PURE__ */ t(
    J,
    {
      title: n ? e("{0} to {1}", [_(n.start_date), _(n.end_date)]) : e("Payslip"),
      subtitle: n?.employee_name,
      onBack: () => a(s.pay),
      actions: /* @__PURE__ */ h(b, { href: _n(i), target: "_blank", rel: "noopener", children: [
        /* @__PURE__ */ t(mn, {}),
        e("Open Payslip")
      ] }),
      loading: o,
      error: l,
      onRetry: c,
      children: n && /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
        /* @__PURE__ */ t(
          j,
          {
            items: [
              { label: e("Gross Pay"), value: $(n.gross_pay, n.currency) },
              { label: e("Total Deduction"), value: $(n.total_deduction, n.currency) },
              { label: e("Net Pay"), value: $(n.net_pay, n.currency) }
            ]
          }
        ),
        /* @__PURE__ */ t(B, { title: e("Earnings"), children: /* @__PURE__ */ t(D, { divided: !0, children: n.earnings.map((r) => /* @__PURE__ */ t(L, { primary: r.component, action: $(r.amount, n.currency) }, r.component)) }) }),
        /* @__PURE__ */ t(B, { title: e("Deductions"), children: /* @__PURE__ */ t(D, { divided: !0, children: n.deductions.map((r) => /* @__PURE__ */ t(L, { primary: r.component, action: $(r.amount, n.currency) }, r.component)) }) })
      ] })
    }
  );
}
function ea() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.timesheets);
  return /* @__PURE__ */ h(
    Z,
    {
      title: e("Timesheets"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: l,
      actions: i?.weekly ? /* @__PURE__ */ h(b, { onClick: () => a(s.week(He(Y()))), children: [
        /* @__PURE__ */ t(Le, {}),
        e("This Week")
      ] }) : void 0,
      children: [
        i && !i.weekly && /* @__PURE__ */ t(E, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer; they show here.") }),
        c && !i?.timesheets.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Le, {}), title: e("No timesheets yet"), description: e("Your timesheets show here, newest first.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i?.timesheets ?? []).map((r) => /* @__PURE__ */ t(
          L,
          {
            primary: e("{0} to {1}", [_(r.start_date), _(r.end_date)]),
            secondary: e("{0} hours", [String(r.total_hours ?? 0)]),
            action: /* @__PURE__ */ t(M, { value: r.docstatus === 1 ? "Approved" : r.custom_approval_state || r.status }),
            onClick: () => a(i?.weekly && r.custom_week_start ? s.week(r.custom_week_start) : s.timesheetRecord(r.name))
          },
          r.name
        )) })
      ]
    }
  );
}
function Ie(a) {
  return a === "Rest day" ? e("Rest Day") : a === "Public holiday" ? e("Public Holiday") : null;
}
function ze(a) {
  const i = ((/* @__PURE__ */ new Date(`${a}T12:00:00Z`)).getUTCDay() + 6) % 7;
  return [e("Monday"), e("Tuesday"), e("Wednesday"), e("Thursday"), e("Friday"), e("Saturday"), e("Sunday")][i];
}
function ta() {
  const a = A(), i = F(), n = He(U().week || Y()), { data: o, isLoading: l, error: c, mutate: r } = N(g.timesheetWeek, { week_start: n }), u = S(g.saveTimesheetWeek), y = S(g.timesheetClaim), [v, m] = T([]), [d, p] = T(() => {
    const w = Y();
    return w >= n && w <= ce(n, 6) ? We(n).indexOf(w) : 0;
  }), [R, x] = T(!1);
  Ve(() => {
    o && (m(o.timesheet?.entries.length ? o.timesheet.entries : [Oe([], o.default_activity_type)]), x(!1));
  }, [o]);
  const H = We(n), f = o?.days[d], q = !!o?.weekly && (!o.timesheet || o.timesheet.can_edit), I = oe(() => (o?.activity_types ?? []).map((w) => ({ value: w, label: w })), [o]), P = (w) => {
    m(w), x(!0);
  }, ee = async (w) => {
    try {
      const O = await u.run({ week_start: n, entries: JSON.stringify(An(v)), send: w ? 1 : 0 });
      return i.success(w ? e("Week sent for approval.") : e("Week saved.")), x(!1), await r(), O;
    } catch {
      return null;
    }
  }, le = o?.timesheet?.can_claim ? /* @__PURE__ */ t(
    b,
    {
      onClick: async () => {
        try {
          a(s.toilRecord(await y.run({ name: o.timesheet.name })));
        } catch {
        }
      },
      loading: y.loading,
      children: e("Claim as Time Off in Lieu")
    }
  ) : q ? /* @__PURE__ */ h("div", { className: "flex gap-2", children: [
    /* @__PURE__ */ t(b, { variant: "outline", loading: u.loading, disabled: !R, onClick: () => ee(!1), children: e("Save") }),
    o?.approval && /* @__PURE__ */ t(b, { loading: u.loading, onClick: () => ee(!0), children: e("Send for Approval") })
  ] }) : void 0;
  return /* @__PURE__ */ t(
    K,
    {
      title: e("Week of {0}", [_(n)]),
      subtitle: e("{0} hours this week", [String(Rn(v))]),
      meta: o?.timesheet && /* @__PURE__ */ t(M, { value: o.timesheet.docstatus === 1 ? "Approved" : o.timesheet.state }),
      onBack: () => a(s.timesheet),
      actions: le,
      loading: l,
      error: c,
      onRetry: r,
      children: o && /* @__PURE__ */ h("div", { className: "flex flex-col gap-4", children: [
        (u.errorMessage || y.errorMessage) && /* @__PURE__ */ t(E, { tone: "error", children: u.errorMessage || y.errorMessage }),
        !o.weekly && /* @__PURE__ */ t(E, { tone: "info", children: e("Your company does not keep weekly timesheets. Fill timesheets in on a computer.") }),
        o.timesheet?.state === "Returned" && o.timesheet.return_reason && /* @__PURE__ */ t(E, { tone: "warning", title: e("Returned to You"), children: o.timesheet.return_reason }),
        /* @__PURE__ */ h("div", { className: "flex items-center justify-between gap-2", children: [
          /* @__PURE__ */ t(we, { label: e("Previous Day"), variant: "outline", onClick: () => d > 0 ? p(d - 1) : a(s.week(ce(n, -7))), children: /* @__PURE__ */ t(un, {}) }),
          /* @__PURE__ */ h("div", { className: "flex flex-col items-center", children: [
            /* @__PURE__ */ t(G, { size: "lg", children: ze(H[d]) }),
            /* @__PURE__ */ t(G, { size: "sm", muted: !0, children: _(H[d]) })
          ] }),
          /* @__PURE__ */ t(we, { label: e("Next Day"), variant: "outline", onClick: () => d < 6 ? p(d + 1) : a(s.week(ce(n, 7))), children: /* @__PURE__ */ t(st, {}) })
        ] }),
        /* @__PURE__ */ h("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ t(he, { children: e("{0} hours entered", [String(St(v, d))]) }),
          f?.attendance_hours !== null && f?.attendance_hours !== void 0 && /* @__PURE__ */ t(he, { variant: "outline", children: e("Attendance {0} hours", [String(f.attendance_hours)]) }),
          f && Ie(f.kind) && /* @__PURE__ */ t(he, { tone: "info", children: Ie(f.kind) }),
          f?.leave && /* @__PURE__ */ t(he, { tone: "warning", children: f.leave_fraction === 0.5 ? e("Half Day of Leave") : e("On Leave") })
        ] }),
        v.map((w) => /* @__PURE__ */ t(Kt, { children: /* @__PURE__ */ h(Zt, { className: "flex flex-col gap-3", children: [
          /* @__PURE__ */ h("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(fe, { htmlFor: `activity-${w.row}`, children: e("Activity Type") }),
            /* @__PURE__ */ t(
              Qt,
              {
                id: `activity-${w.row}`,
                value: w.activity_type,
                options: I,
                disabled: !q,
                onValueChange: (O) => P(v.map((C) => C.row === w.row ? { ...C, activity_type: O } : C))
              }
            )
          ] }),
          /* @__PURE__ */ h("div", { className: "flex flex-col gap-1", children: [
            /* @__PURE__ */ t(fe, { htmlFor: `description-${w.row}`, children: e("Description") }),
            /* @__PURE__ */ t(
              Ne,
              {
                id: `description-${w.row}`,
                value: w.description ?? "",
                disabled: !q,
                onChange: (O) => P(v.map((C) => C.row === w.row ? { ...C, description: O.target.value } : C))
              }
            )
          ] }),
          /* @__PURE__ */ h("div", { className: "flex items-end gap-2", children: [
            /* @__PURE__ */ h("div", { className: "flex flex-1 flex-col gap-1", children: [
              /* @__PURE__ */ t(fe, { htmlFor: `hours-${w.row}`, children: e("Hours on {0}", [ze(H[d])]) }),
              /* @__PURE__ */ t(
                Ne,
                {
                  id: `hours-${w.row}`,
                  type: "number",
                  inputMode: "decimal",
                  min: 0,
                  max: 24,
                  step: 0.25,
                  value: w.hours[d] ? String(w.hours[d]) : "",
                  disabled: !q,
                  onChange: (O) => P(Nn(v, w.row, d, O.target.value))
                }
              )
            ] }),
            q && v.length > 1 && /* @__PURE__ */ t(we, { label: e("Remove Line"), variant: "ghost", onClick: () => P(v.filter((O) => O.row !== w.row)), children: /* @__PURE__ */ t(gn, {}) })
          ] })
        ] }) }, w.row)),
        q && /* @__PURE__ */ h("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ h(b, { variant: "outline", onClick: () => P([...v, Oe(v, o.default_activity_type)]), children: [
            /* @__PURE__ */ t(se, {}),
            e("Add Line")
          ] }),
          o.previous_entries.length > 0 && /* @__PURE__ */ h(b, { variant: "outline", onClick: () => P(xn(o.previous_entries)), children: [
            /* @__PURE__ */ t(hn, {}),
            e("Copy Last Week")
          ] })
        ] }),
        o.checks.length > 0 && /* @__PURE__ */ t(B, { title: e("Weekly Check"), children: /* @__PURE__ */ t(D, { divided: !0, children: o.checks.map((w) => /* @__PURE__ */ t(L, { primary: w }, w)) }) })
      ] })
    }
  );
}
function na() {
  const a = A(), i = X(U().name), { data: n, isLoading: o, error: l, mutate: c } = N(g.timesheetRecord, { name: i });
  return /* @__PURE__ */ t(
    J,
    {
      title: e("Timesheet"),
      subtitle: n && (n.mine ? i : n.employee_name),
      meta: n && /* @__PURE__ */ t(M, { value: n.docstatus === 1 ? "Approved" : n.state }),
      onBack: () => a(s.timesheet),
      actions: n?.mine && n.week_start ? /* @__PURE__ */ t(b, { onClick: () => a(s.week(n.week_start)), children: e("Open the Week") }) : void 0,
      loading: o,
      error: l,
      onRetry: c,
      children: n && /* @__PURE__ */ h("div", { className: "flex flex-col gap-4", children: [
        /* @__PURE__ */ t(
          j,
          {
            items: [
              { label: e("From"), value: _(n.start_date) },
              { label: e("To"), value: _(n.end_date) },
              { label: e("Total Hours"), value: String(n.total_hours ?? 0) }
            ]
          }
        ),
        /* @__PURE__ */ t(D, { divided: !0, children: n.lines.map((r, u) => /* @__PURE__ */ t(L, { primary: e("{0} · {1} hours", [_(r.date), String(r.hours)]), secondary: [r.activity_type, r.description].filter(Boolean).join(" · ") }, u)) })
      ] })
    }
  );
}
function aa() {
  const a = A(), { data: i, isLoading: n, error: o, mutate: l, hasLoaded: c } = N(g.toilList);
  return /* @__PURE__ */ h(
    Z,
    {
      title: e("Time Off in Lieu"),
      onBack: () => a(""),
      loading: n,
      error: o,
      onRetry: l,
      actions: i?.eligible ? /* @__PURE__ */ h(b, { onClick: () => a(s.toilNew), children: [
        /* @__PURE__ */ t(se, {}),
        e("Claim Time Off")
      ] }) : void 0,
      children: [
        i && !i.eligible && /* @__PURE__ */ t(E, { tone: "info", children: e("Your grade does not bank extra hours as time off. Ask HR if you think it should.") }),
        i?.eligible && /* @__PURE__ */ h(nt, { columns: 2, children: [
          /* @__PURE__ */ t(xe, { label: e("Days Left"), value: String(i.left) }),
          /* @__PURE__ */ t(
            xe,
            {
              label: e("Lapsing in 30 Days"),
              value: String(i.lapsing),
              hint: i.first_lapse ? e("First on {0}", [_(i.first_lapse)]) : void 0
            }
          )
        ] }),
        c && !i?.claims.length ? /* @__PURE__ */ t(Q, { icon: /* @__PURE__ */ t(Se, {}), title: e("No claims yet"), description: e("Claim the extra hours you worked, a day at a time.") }) : /* @__PURE__ */ t(D, { divided: !0, children: (i?.claims ?? []).map((r) => /* @__PURE__ */ t(
          L,
          {
            primary: e("{0} hours · {1} days", [String(r.total_hours ?? 0), String(r.days ?? 0)]),
            secondary: r.status === "Approved" && r.lapses_on ? e("{0} days left, usable until {1}", [String(r.days_left ?? 0), _(r.lapses_on)]) : _(r.creation),
            action: /* @__PURE__ */ t(M, { value: r.status }),
            onClick: () => a(s.toilRecord(r.name))
          },
          r.name
        )) })
      ]
    }
  );
}
const je = () => ({ work_date: "", hours: null, work_done: "" });
function oa() {
  const a = A(), i = F(), [n] = Ue(), o = n.get("claim"), l = N(g.toilList), c = N(g.toilRecord, { name: o ?? "" }, { enabled: !!o }), r = S(g.saveToilClaim), u = Ft(), [y, v] = T(!1), [m, d] = T(null), p = ie({ defaultValues: { lines: [je()], note: "" } });
  Ve(() => {
    c.data && p.reset({ lines: c.data.lines.map((f) => ({ work_date: f.work_date, hours: f.hours, work_done: f.work_done })), note: c.data.note ?? "" });
  }, [c.data, p]);
  const R = async () => {
    if (l.data) {
      v(!0), d(null);
      try {
        const f = l.data.from_attendance ? "Attendance" : "Timesheet", q = Y(), I = await u.get(g.extraTime, { employee: l.data.employee, from_date: ce(q, -30), to_date: q, source: f }) ?? [], P = p.getValues("lines").filter((ee) => ee.work_date);
        p.setValue("lines", Bn(P, I), { shouldDirty: !0 }), d(I.length ? e("{0} days found in the last 30 days. Say what the work was on each.", [String(I.length)]) : e("The records show no extra hours you have not claimed in the last 30 days."));
      } catch {
        d(e("The records could not be read. Enter the days yourself."));
      } finally {
        v(!1);
      }
    }
  }, x = async (f) => {
    const q = await r.run({ lines: JSON.stringify(f.lines.filter((I) => I.work_date)), note: f.note, name: o ?? void 0 });
    i.success(e("Claim saved. Send it when it is ready.")), a(s.toilRecord(q));
  }, H = l.data && (l.data.from_attendance || l.data.from_timesheets);
  return /* @__PURE__ */ h(
    K,
    {
      title: o ? e("Change Claim") : e("Claim Time Off"),
      onBack: () => a(o ? s.toilRecord(o) : s.toil),
      loading: l.isLoading || c.isLoading,
      error: l.error ?? c.error,
      actions: H ? /* @__PURE__ */ t(b, { variant: "outline", loading: y, onClick: R, children: e("Fill from Records") }) : void 0,
      children: [
        m && /* @__PURE__ */ t(E, { tone: "info", children: m }),
        /* @__PURE__ */ h(re, { form: p, onSubmit: x, children: [
          /* @__PURE__ */ t(
            Xe,
            {
              name: "lines",
              label: e("Days Worked"),
              minRows: 1,
              addLabel: e("Add a Day"),
              newRow: je,
              renderRow: (f) => /* @__PURE__ */ h(de, { children: [
                /* @__PURE__ */ t(te, { name: f("work_date"), label: e("Date"), required: !0, maxDate: Y() }),
                /* @__PURE__ */ t(Ee, { name: f("hours"), label: e("Hours Worked"), min: 0, max: 24, step: 0.25 }),
                /* @__PURE__ */ t(z, { name: f("work_done"), label: e("Work Done"), required: !0, multiline: !0, rows: 2 })
              ] })
            }
          ),
          /* @__PURE__ */ t(z, { name: "note", label: e("Note"), multiline: !0, rows: 2, hint: e("Anything your approver should know about these days.") }),
          /* @__PURE__ */ t(ue, { submitLabel: e("Save Claim"), onCancel: () => a(o ? s.toilRecord(o) : s.toil) })
        ] })
      ]
    }
  );
}
function ia() {
  const a = A(), i = F(), n = X(U().name), { data: o, isLoading: l, error: c, mutate: r } = N(g.toilRecord, { name: n }), u = S(g.toilAction), y = async (m) => {
    try {
      await u.run({ name: n, action: m }), i.success(e("Claim sent.")), await r();
    } catch {
    }
  }, v = o && /* @__PURE__ */ h("div", { className: "flex gap-2", children: [
    o.can_edit && /* @__PURE__ */ t(b, { variant: "outline", onClick: () => a(`${s.toilNew}?claim=${encodeURIComponent(n)}`), children: e("Change") }),
    o.actions.map((m) => /* @__PURE__ */ t(b, { loading: u.loading, onClick: () => y(m), children: m === "Send for Authorisation" ? e("Send for Authorisation") : e("Send for Approval") }, m)),
    o.mine && o.status === "Approved" && (o.days_left ?? 0) > 0 && o.leave_type && /* @__PURE__ */ t(b, { onClick: () => a(`${s.leaveNew}?type=${encodeURIComponent(o.leave_type ?? "")}`), children: e("Apply for Leave") })
  ] });
  return /* @__PURE__ */ t(
    J,
    {
      title: e("Time Off in Lieu Claim"),
      subtitle: o && !o.mine ? o.employee_name : n,
      meta: o && /* @__PURE__ */ t(M, { value: o.status }),
      onBack: () => a(s.toil),
      actions: v,
      loading: l,
      error: c,
      onRetry: r,
      children: o && /* @__PURE__ */ h("div", { className: "flex flex-col gap-6", children: [
        u.errorMessage && /* @__PURE__ */ t(E, { tone: "error", children: u.errorMessage }),
        o.stage.items.length > 0 && /* @__PURE__ */ t(E, { tone: o.stage.tone, children: /* @__PURE__ */ t("div", { className: "flex flex-col gap-1", children: o.stage.items.map((m) => /* @__PURE__ */ h(G, { children: [
          /* @__PURE__ */ h("strong", { children: [
            m.label,
            ":"
          ] }),
          " ",
          m.text
        ] }, m.label)) }) }),
        /* @__PURE__ */ t(
          j,
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
        /* @__PURE__ */ t(B, { title: e("Days Worked"), children: /* @__PURE__ */ t(D, { divided: !0, children: o.lines.map((m) => /* @__PURE__ */ t(
          L,
          {
            primary: e("{0} · {1} hours", [_(m.work_date), String(m.hours ?? m.planned_hours ?? 0)]),
            secondary: [m.work_done, m.supported_by ?? ""].filter(Boolean).join(" · ")
          },
          m.work_date
        )) }) })
      ] })
    }
  );
}
const ra = [
  { path: "leave", element: /* @__PURE__ */ t(On, {}) },
  { path: "leave/new", element: /* @__PURE__ */ t(Fn, {}) },
  { path: "leave/:name", element: /* @__PURE__ */ t(In, {}) },
  { path: "cover", element: /* @__PURE__ */ t($n, {}) },
  { path: "cover/:name", element: /* @__PURE__ */ t(En, {}) },
  { path: "toil", element: /* @__PURE__ */ t(aa, {}) },
  { path: "toil/new", element: /* @__PURE__ */ t(oa, {}) },
  { path: "toil/:name", element: /* @__PURE__ */ t(ia, {}) },
  { path: "timesheet", element: /* @__PURE__ */ t(ea, {}) },
  { path: "timesheet/week/:week", element: /* @__PURE__ */ t(ta, {}) },
  { path: "timesheet/:name", element: /* @__PURE__ */ t(na, {}) },
  { path: "expenses", element: /* @__PURE__ */ t(Vn, {}) },
  { path: "expenses/new", element: /* @__PURE__ */ t(Un, {}) },
  { path: "expenses/:name", element: /* @__PURE__ */ t(Jn, {}) },
  { path: "advances", element: /* @__PURE__ */ t(Gn, {}) },
  { path: "advances/new", element: /* @__PURE__ */ t(Kn, {}) },
  { path: "advances/:name", element: /* @__PURE__ */ t(Zn, {}) },
  { path: "pay", element: /* @__PURE__ */ t(Qn, {}) },
  { path: "pay/:name", element: /* @__PURE__ */ t(Xn, {}) },
  { path: "check-in", element: /* @__PURE__ */ t(Ln, {}) },
  { path: "attendance", element: /* @__PURE__ */ t(Sn, {}) },
  { path: "attendance/new", element: /* @__PURE__ */ t(Mn, {}) },
  { path: "attendance/:name", element: /* @__PURE__ */ t(Fe, { doctype: "Attendance Request" }) },
  { path: "shifts", element: /* @__PURE__ */ t(Wn, {}) },
  { path: "shifts/new", element: /* @__PURE__ */ t(qn, {}) },
  { path: "shifts/:name", element: /* @__PURE__ */ t(Fe, { doctype: "Shift Request" }) },
  { path: "me", element: /* @__PURE__ */ t(zn, {}) },
  { path: "me/payout/new", element: /* @__PURE__ */ t(jn, {}) },
  { path: "me/payout/:name", element: /* @__PURE__ */ t(Yn, {}) }
], ya = Ht({
  key: "seal_hrms.my_hr",
  home: Tn,
  routes: ra,
  records: at,
  settings: [{ key: "hr_notifications", label: "HR", kind: "push-category" }]
});
export {
  ra as ROUTES,
  ya as default
};
