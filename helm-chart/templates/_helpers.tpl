{{- define "fastapi-app.name" -}}
{{- .Chart.Name -}}
{{- end }}

{{- define "fastapi-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride }}
{{- else }}
{{- printf "%s" .Release.Name }}
{{- end }}
{{- end }}

{{- define "fastapi-app.labels" -}}
app.kubernetes.io/name: {{ include "fastapi-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}