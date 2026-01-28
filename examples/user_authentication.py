"""User authentication flow example.

Demonstrates a class-based flow with MFA branching and multiple
decision points.
"""

from flowdoc import flow, step


@flow(name="User Authentication", description="Authenticate user with optional MFA")
class AuthFlow:
    @step(name="Receive Credentials", description="Accept username and password")
    def receive_credentials(self, credentials: dict) -> dict:
        return self.verify_password(credentials)

    @step(name="Verify Password", description="Check password against stored hash")
    def verify_password(self, credentials: dict) -> dict:
        if credentials.get("password_valid"):
            return self.check_mfa_required(credentials)
        else:
            return self.reject_login(credentials)

    @step(name="Check MFA Required", description="Determine if MFA is enabled for user")
    def check_mfa_required(self, credentials: dict) -> dict:
        if credentials.get("mfa_enabled"):
            return self.verify_mfa_token(credentials)
        else:
            return self.grant_access(credentials)

    @step(name="Verify MFA Token", description="Validate the MFA token")
    def verify_mfa_token(self, credentials: dict) -> dict:
        if credentials.get("mfa_valid"):
            return self.grant_access(credentials)
        else:
            return self.reject_login(credentials)

    @step(name="Grant Access", description="Create session and grant user access")
    def grant_access(self, credentials: dict) -> dict:
        return {"status": "authenticated", "user": credentials.get("username")}

    @step(name="Reject Login", description="Deny access and log failed attempt")
    def reject_login(self, credentials: dict) -> dict:
        return {"status": "rejected", "user": credentials.get("username")}
