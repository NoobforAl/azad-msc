workspace "Course Registration Platform" "C4 sketch of the running project (state m0 plus the planned parts)" {

    model {
        student = person "Student" "Browses courses and registers"
        registrar = person "Registrar" "Reads enrollment statistics"

        platform = softwareSystem "Course Registration Platform" "Lets students register for courses" {
            web = container "Web / CLI client" "Planned" "any HTTP client" "Client"
            api = container "registration-api" "Serves GET /healthz and GET /courses (m0)" "Go 1.22, net/http" "Service"
            analytics = container "analytics" "Computes course fill rates (stub in m0)" "Python 3.8+" "Service"
            db = container "PostgreSQL" "Planned for module 04; m0 uses an in-memory catalog" "PostgreSQL" "Store"
            broker = container "Message broker" "Planned for module 04" "to be chosen in an ADR" "Infra"
        }

        student -> web "Uses"
        registrar -> analytics "Reads reports from"
        web -> api "Calls" "HTTP/JSON"
        api -> db "Reads and writes" "SQL"
        api -> broker "Publishes enrollment events"
        broker -> analytics "Delivers events"
        analytics -> db "Reads"
    }

    views {
        systemContext platform "context" {
            include *
            autolayout lr
        }
        container platform "containers" {
            include *
            autolayout lr
        }
        styles {
            element "Client" {
                background #0E7490
                color #ffffff
            }
            element "Service" {
                background #B45309
                color #ffffff
            }
            element "Infra" {
                background #6D28D9
                color #ffffff
            }
            element "Store" {
                background #047857
                color #ffffff
                shape Cylinder
            }
        }
    }
}
