import { type RouteConfig, index, layout, route } from "@react-router/dev/routes";

export default [
    layout("withNav.tsx", [
        index("routes/home.tsx"),
        route("login", "routes/login.tsx"),
        route("register", "routes/register.tsx"),
    ]),
    route("dashboard", "routes/dashboard.tsx"),
] satisfies RouteConfig;
