import alsaaudio, time, audioop
from collections import deque
from Tkinter import *
import numpy
import analyse

class Main(object):
    def __init__(self, **kwargs):

        self.setupMics()

        self.master = Tk()             
        self.master.overrideredirect(1)
        
        self.w = self.master.winfo_screenwidth()
        self.h = self.master.winfo_screenheight()
        
        self.canvas = Canvas(self.master, width=self.w, height=self.h)
        self.canvas.configure(bg="black", highlightthickness=0, cursor='none')
        self.master.configure(bg="red", borderwidth=0)
        self.canvas.pack()
        self.master.update()

        self.startScreen()

    def setupMics (self):

        cards = alsaaudio.cards()
        print cards

        # the first card is internal Intel
        # we need the rest
        self.mics = []
        for i in range(len(cards) - 1):
            
            inp  = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, "hw:CARD=" + cards[1 + i])
            
            inp.setchannels(1)
            inp.setrate(44100)
            inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
            inp.setperiodsize(1024)
            
            self.mics.append(inp)

    def checkLevels(self):        
        l = False
        
        try:
            l,data = self.mics[0].read()
        except:
            print "error"
            
        if not l or len(data) < 2048:
            return (False, 0, 0)

        samps = numpy.fromstring(data, dtype=numpy.int16)

        pitch = analyse.musical_detect_pitch(samps)
        loudness = min(0, max(-32, analyse.loudness(samps)))
        
        return (True, pitch,loudness)

    def run(self):

        while True:
        
            self.currentApp.run()                


    def startPong(self):
    
        self.currentApp.finish()
        self.currentApp = SongPong(self)

    def startScreen(self):
        self.currentApp = StartScreen(self)

    


class StartScreen(object):
    def __init__(self, main, **kwargs):
        
        self.main = main
        canvas = main.canvas
        w = main.w
        w2 = w/2
        h = main.h
        h2 = h/2
        self.maxSize = min(w, h)
        
        self.highLevel = 0
        self.setHighLevelAt = 0                            

        self.frames = deque()

        self.lastWidth = 0
        self.pitch = 0
        
        self.current_rectangle = False
        
        canvas.create_text(w2, 15, text="OpenMusicGallery.net", fill="#0000FF", font="Helvetica 16", )        

        self.highest_shape = canvas.create_oval(w2 - self.lastWidth /2,  h2 - self.lastWidth /2, 
            w2 + self.lastWidth /2,  h2 + self.lastWidth /2, outline="#DDDD00", width=3)        

        self.current_shape = canvas.create_oval(w2 - self.lastWidth /2,  h2 - self.lastWidth /2, 
            w2 + self.lastWidth /2,  h2 + self.lastWidth /2, fill="blue")        

        self.loudness_caption = canvas.create_text(5, h, text="Volume: ", 
                fill="purple", font="Helvetica 16", anchor="sw")
        self.note_caption = canvas.create_text(5, h - 18, text="Note: ", 
                fill="purple", font="Helvetica 16", anchor="sw")

        self.details_caption = canvas.create_text(w, h, text="", 
                fill="purple", font="Helvetica 16", anchor="se")
        self.details2_caption = canvas.create_text(w, h - 18, text="", 
                fill="purple", font="Helvetica 16", anchor="se")

        self.lastSpike = 0
        self.spikes = 0
        
        self.lastFrame = False
        self.secondToLastFrame = False

        self.main.canvas.config(bg="black")

    def run(self):
        newFrame = self.checkLevels()
        
        if newFrame:
            lastFrame = self.lastFrame
            secondToLastFrame = self.secondToLastFrame
            
            wasQuiet = ((lastFrame and lastFrame.loudness < -28) or 
                        (secondToLastFrame and secondToLastFrame.loudness < -28))

            isLoud = newFrame.loudness > -18
            
            if wasQuiet and isLoud:
                if self.lastSpike > 0 and time.time() - self.lastSpike < 0.7:
                    self.spikes += 1
                else:
                    self.spikes = 1                

                if self.spikes >= 3:
                    self.main.startPong()
                    return
                    
                self.lastSpike = time.time()
                self.main.canvas.config(bg="red")
            elif self.lastSpike > 0 and time.time() - self.lastSpike > 0.5:
                self.main.canvas.config(bg="black")
            elif self.lastSpike > 0 and time.time() - self.lastSpike > 0.75:
                spikes = 0

            self.secontToLastFrame = lastFrame    
            self.lastFrame = newFrame

        self.animation()


    def finish(self):
        self.main.canvas.delete("all")

                
    def checkLevels(self):
    
        l,pitch,loudness = self.main.checkLevels()    
    
        if not l:
            return None
        
        colorWidth = (loudness + 32) / 32 * self.maxSize

        self.lastWidth = colorWidth

        main = self.main
        rect = main.canvas.create_oval(main.w/2 - colorWidth /2,  main.h/2 - colorWidth /2, 
            main.w/2 + colorWidth /2,  main.h/2 + colorWidth /2, fill="#000080")

        frame = SoundFrame(colorWidth, rect, colorWidth, loudness=loudness, pitch=pitch)
        self.frames.append(frame)

        if len(self.frames) > 60:
            main.canvas.delete(self.frames.popleft().rectangle)
                        
        if self.highLevel < colorWidth:
            self.highLevel = colorWidth
        elif self.highLevel > 0:
            self.highLevel = self.highLevel - 6

        return frame


    
    def animation(self):

        w2 = self.main.w / 2
        h2 = self.main.h / 2

        canvas = self.main.canvas        
        canvas.coords(self.highest_shape, w2 - self.highLevel /2,  h2 - self.highLevel /2, 
            w2 + self.highLevel /2,  h2 + self.highLevel /2)        
        canvas.tag_raise(self.highest_shape)

        canvas.coords(self.current_shape, w2 - self.lastWidth /2,  h2 - self.lastWidth /2, 
            w2 + self.lastWidth /2,  h2 + self.lastWidth /2)        
        canvas.tag_raise(self.current_shape)

        #canvas.itemconfig(self.loudness_caption, text="vol " + str(self.loudness))
        #canvas.itemconfig(self.note_caption, text="note " + str(self.pitch))

        for i in range(len(self.frames)):
            frame = self.frames[i]
            if frame.width > 1:
                frame.width = frame.width - 1
                width = frame.width
                canvas.coords(frame.rectangle, w2 - width /2,  
                    h2 - width /2, 
                    w2 + width /2,  h2 + width /2)

        self.main.master.update()

class SongPong(object):
    def __init__(self, main, **kwargs):
        self.main = main

        self.enteredGameAt = time.time()

        self.dx = -4
        self.dy = 4
        self.x = 0
        self.y = 0
        self.w = 24

        self.main.canvas.config(bg="green")        
        self.ball = main.canvas.create_oval(0, 0, 0, 0, fill="white", outline="black")
        
        self.title = main.canvas.create_text(main.w / 2, main.h / 2 - 10, text="Song Pong")
        self.sing_a_note = main.canvas.create_text(main.w / 2, main.h / 2 + 10, text="Sing The Most Natural Note You Can")

        self.stage = 0        
        
        self.refLen = 10
        
        self.referenceNotes = deque(maxlen=self.refLen)
        
        self.lastNoteP = 0

    def run(self):
    
        h2 = self.main.h / 2
        w2 = self.main.w / 2
        
        bw2 = self.w / 2

        note = self.getReferenceNote()

        if self.stage == 0:
            if note > -1:
                self.referenceNote = note
                self.main.canvas.itemconfig(self.title, text="Note is " + str(note))
                self.main.canvas.itemconfig(self.sing_a_note, text="Singer higer or lower to move the paddle")
                self.stage = 1
                self.enteredGameAt = time.time()
                
                self.paddle = self.main.canvas.create_rectangle(self.main.w - 15, self.main.h / 3,
                                                  self.main.w - 5, self.main.h / 3 * 2,
                                                  fill="black")
            
        elif self.stage == 1:

            h6 = self.main.h / 6
            noteP = self.lastNoteP
            if note > -1:
                noteP = (self.referenceNote - note) * 20
                #if note > self.referenceNote + 1:
                self.main.canvas.coords(self.paddle, 
                        self.main.w - 15, h2 + noteP - h6,
                        self.main.w - 5,  h2 + noteP + h6)
                self.lastNoteP = noteP


            if self.dx < 0 and self.x - self.dx < -w2:
                self.dx = self.dx * -1
            if self.dx > 0 and self.x >= w2 - 15:
                if noteP - h6 < self.y < noteP + h6:
                    self.dx =  self.dx * -1
                else:
                    self.pointScored()
            
            if (self.dy > 0 and self.y + self.dy >= h2) or \
                (self.dy < 0 and self.y - self.dy <= -h2):
                self.dy = self.dy * -1
        
            self.x += self.dx
            self.y += self.dy
        
            self.main.canvas.coords(self.ball, 
                    w2 + self.x - bw2,
                    h2 + self.y - bw2, 
                    w2 + self.x + bw2,
                    h2 + self.y + bw2)

            if self.enteredGameAt > 0 and time.time() - self.enteredGameAt > 60:
                self.main.startScreen()

        self.main.master.update()


    def getReferenceNote(self):
        l,pitch,loudness = self.main.checkLevels()
        
        if l and pitch:
            self.referenceNotes.append(pitch)
            
            if len(self.referenceNotes) == self.refLen:
                minPitch = self.referenceNotes[0]
                maxPitch = self.referenceNotes[0]
                for i in range(self.refLen):
                    v = self.referenceNotes[i]
                    if v < minPitch: minPitch = v
                    if v > maxPitch: maxPitch = v
                    
                if maxPitch - minPitch < 1:
                    return (maxPitch + minPitch) / 2
        
        return -1
        
    def pointScored(self):
        self.main.startScreen()            
            

class SoundFrame(object):
    def __init__(self, value, rectangle, width, loudness=-32, pitch=0, **kwargs):
        self.value = value
        self.rectangle = rectangle
        self.width = width
        self.loudness = loudness
        self.pitch = pitch
        

main = Main()
main.run()



