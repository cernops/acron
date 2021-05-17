job "__PROJECT_NAME__-__JOB_NAME__" {
  meta {
    description = "__DESCRIPTION__"
  }
  type = "batch"
  periodic {
    cron             = "__CRON__"
    prohibit_overlap = true
  }
  task "ssh" {
    driver = "exec"
    user = "nomad"
    config {
      command = "/usr/libexec/acron/ssh_run"
      args    = ["__PROJECT_NAME__", "__TARGET_HOST__", "__COMMAND__"]
    }
  }
}
