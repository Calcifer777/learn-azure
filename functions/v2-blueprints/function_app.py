import azure.functions as func
import azure.durable_functions as df

import triggers
import activities
import orchestrators


app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_blueprint(triggers.bp)
app.register_blueprint(activities.bp)
app.register_blueprint(orchestrators.bp)
