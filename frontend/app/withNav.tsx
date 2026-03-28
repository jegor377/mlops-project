import { Outlet } from "react-router";
import Nav from "./nav";

export default function WithNav() {
    return (
        <div>
            <Nav />
            <Outlet />
        </div>
    );
}