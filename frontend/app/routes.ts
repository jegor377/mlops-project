import { type RouteConfig, index, layout, route } from "@react-router/dev/routes";

export default [
    layout("withNav.tsx", [
        index("routes/home.tsx"),
        route("login", "routes/login.tsx"),
        route("register", "routes/register.tsx"),
        route("forgot-password", "routes/forgot-password.tsx"),
        route("reset-password", "routes/reset-password.tsx"),
    ]),
    route("dashboard", "routes/dashboard.tsx"),
] satisfies RouteConfig;
