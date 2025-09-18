apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      imagePullSecrets:
        - name: regcred
      containers:
      - name: backend
        image: ${BACKEND_IMAGE}
        ports:
        - containerPort: 8000
        env:
          - name: IONOS_API_KEY
            valueFrom:
              secretKeyRef:
                name: secrets
                key: IONOS_API_KEY
          - name: TAVILY_API_KEY
            valueFrom:
              secretKeyRef:
                name: secrets
                key: TAVILY_API_KEY
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: LoadBalancer
  selector:
    app: backend
  ports:
    - port: 8000
      targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: streamlit
spec:
  replicas: 1
  selector:
    matchLabels:
      app: streamlit
  template:
    metadata:
      labels:
        app: streamlit
    spec:
      imagePullSecrets:
        - name: regcred
      containers:
      - name: streamlit
        image: ${FRONTEND_IMAGE}
        ports:
        - containerPort: 8501
        env:
          - name: IONOS_API_KEY
            valueFrom:
              secretKeyRef:
                name: secrets
                key: IONOS_API_KEY
---
apiVersion: v1
kind: Service
metadata:
  name: streamlit-service
spec:
  type: LoadBalancer
  selector:
    app: streamlit
  ports:
    - port: 8501
      targetPort: 8501
