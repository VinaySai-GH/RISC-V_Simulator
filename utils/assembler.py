class Assembler:
    def __init__(self):
          self.labels={}
          self.instructions=[]

    def load(self,filepath):
        with open(filepath,"r") as f:
            lines=f.readlines()

            cleaned=[]
            for line in lines:
                if "#" in line:
                    line=line[:line.index("#")]

                line=line.strip()

                if not line:
                    continue

                if ":" in line:
                    parts=line.split(":",1)
                    label=parts[0].strip()
                    rest=parts[1].strip()

                    self.labels[label]=len(cleaned)
                   
                    if rest:
                        cleaned.append(rest)
                for line in cleaned:
                    parsed =self.parse_line(line)
                    self.instructions.append(parsed)

                return self.instructions,self.labels
            
    def parse_line(self,line):
        parts=line.split(None,1)
        op=parts[0].upper().strip()
        operands=[]
        if len(parts)>1:
            operands=[x.strip() for x in parts[1].split(",")]
            return {"op":op,"operands":operands}


