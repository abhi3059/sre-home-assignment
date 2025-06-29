{{- define "fastapi-app.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end }}
