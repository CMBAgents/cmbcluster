{{/*
Expand the name of the chart.
*/}}
{{- define "cmbcluster.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "cmbcluster.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "cmbcluster.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "cmbcluster.labels" -}}
helm.sh/chart: {{ include "cmbcluster.chart" . }}
{{ include "cmbcluster.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "cmbcluster.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cmbcluster.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "cmbcluster.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cmbcluster.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Backend fullname
*/}}
{{- define "cmbcluster.backend.fullname" -}}
{{- printf "%s-backend" (include "cmbcluster.fullname" .) }}
{{- end }}

{{/*
Frontend fullname
*/}}
{{- define "cmbcluster.frontend.fullname" -}}
{{- printf "%s-frontend" (include "cmbcluster.fullname" .) }}
{{- end }}
